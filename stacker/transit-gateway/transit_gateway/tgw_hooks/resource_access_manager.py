"""Hook for AWS RAM since it is not supported by CFN yet."""
import logging

from botocore.exceptions import ClientError
from stacker.session_cache import get_session
from stacker.variables import Variable, resolve_variables

LOGGER = logging.getLogger(__name__)


def _stack_output_lookup_handler(provider, context, lookup):
    """Makeshift lookup resolver."""
    lookup = lookup.strip('${}').split(' ')
    lookup_name = lookup[0]
    stack_name = lookup[1].split('::')[0]
    output_name = lookup[1].split('::')[1]

    session = get_session(provider.region)
    client = session.client('cloudformation')

    if lookup_name in ['rxref', 'output']:
        stack_name = '{}-{}'.format(
            context.namespace, stack_name
        )

    try:
        response = client.describe_stacks(
            StackName=stack_name
        )['Stacks'][0]
    except ClientError:
        return None

    lookup_resolved = [
        output.get('OutputValue') for output in response['Outputs']
        if output.get('OutputKey') == output_name
    ][0]

    return lookup_resolved


def _find_resource_share(client, name):  # noqa
    """Wrapper for finding a resource share."""
    log_prefix = 'share_transit_gateway: '

    try:
        response = client.get_resource_shares(
            name=name,
            resourceOwner='SELF'
        )['resourceShares']

        ignore_statuses = [
            'FAILED', 'DELETING', 'DELETED'
        ]

        for share in response:
            if share.get('status') not in ignore_statuses:
                return share['resourceShareArn']
    except (IndexError, ClientError) as err:
        LOGGER.error(log_prefix + str(err))

    return None


def _account_id(provider, context):
    return get_session(provider.region).client(
        'sts'
    ).get_caller_identity().get('Account')


def unshare_transit_gateway(provider, context, **kwargs):
    """Unshares a Transit Gateway with other accounts."""
    log_prefix = 'unshare_transit_gateway: '

    name = kwargs.get('share_name', 'transit-gateway-share')

    session = get_session(provider.region)
    client = session.client('ram')

    share_arn = _find_resource_share(client, name)

    if share_arn is not None:
        try:
            client.delete_resource_share(
                resourceShareArn=share_arn
            )
            LOGGER.info(log_prefix + '{} share deleted'.format(name))
        except ClientError as err:
            LOGGER.error(log_prefix + err)
            return False
    else:
        LOGGER.info(log_prefix + '{} share does not exist'.format(name))
    return True


def accept_share(provider, context, **kwargs):
    """Accepts a RAM share.

    Not needed when sharing within an organization.
    """
    log_prefix = 'accept_share: '

    accept_from = kwargs['accept_from_accounts']
    name = kwargs.get('share_name', 'transit-gateway-share')

    session = get_session(provider.region)
    client = session.client('ram')

    ram_invites = client.get_resource_share_invitations()

    for invite in ram_invites['resourceShareInvitations']:
        if invite['senderAccountId'] in accept_from and \
                invite['resourceShareName'] == name:
            if invite['status'] == 'PENDING':
                client.accept_resource_share_invitation(
                    resourceShareInvitationArn=invite[
                        'resourceShareInvitationArn'
                    ]
                )
                LOGGER.info(
                    log_prefix + 'invite found and accepted for {}'.format(
                        name
                    )
                )
                return True
            elif invite['status'] == 'ACCEPTED':
                LOGGER.info(
                    log_prefix + 'invite for {} share is already '
                    'accepted.'.format(
                        name
                    )
                )
                return True
            elif invite['status'] == 'REJECTED':
                LOGGER.error(
                    log_prefix + 'invite for {} share was rejected.'.format(
                        name
                    )
                )
                return False
            elif invite['status'] == 'EXPIRED':
                LOGGER.error(
                    log_prefix + 'invite for {} share has expired.'.format(
                        name
                    )
                )
                return False

    LOGGER.info(
        '%s + no share invites found for account and name provided', log_prefix
    )

    if _account_id(provider, context) in accept_from:
        return True

    return False


def get_variables(variables, provider, context):
    """Used for Lookups in Post-Build Hook."""
    converted_variables = [
        Variable(k, v) for k, v in variables.items()
    ]
    resolve_variables(
        converted_variables, context, provider
    )
    return {v.name: v.value for v in converted_variables}


def attach_customer_gateway_to_transit_gateway(provider, context, **kwargs):
    """Attaches Customer Gateway to Transit Gateway."""
    variables = get_variables(kwargs, provider, context)
    session = get_session(provider.region)
    client = session.client('ec2')

    customer_gateway_id = variables.get('customer_gateway_id')
    transit_gateway_id = variables.get('transit_gateway_id')

    LOGGER.info('Using Customer Gateway %s and Transit Gateway %s',
                customer_gateway_id, transit_gateway_id)

    response = client.describe_vpn_connections(
        Filters=[
            {
                'Name': 'customer-gateway-id',
                'Values': [
                    customer_gateway_id
                ]
            },
            {
                'Name': 'transit-gateway-id',
                'Values': [
                    transit_gateway_id
                ]
            },
            {
                'Name': 'state',
                'Values': [
                    'available',
                    'pending'
                ]
            },
        ]
    )

    if response['VpnConnections']:
        LOGGER.info('Transit Gateway VPN Attachment Already Exists')
        return response['VpnConnections']

    client.create_vpn_connection(
        CustomerGatewayId=customer_gateway_id,
        TransitGatewayId=transit_gateway_id,
        Type='ipsec.1',
        Options={
            'StaticRoutesOnly': True
        }
    )
    LOGGER.info('Attached Customer Gateway %s to Transit Gateway %s',
                customer_gateway_id, transit_gateway_id)
    return True
