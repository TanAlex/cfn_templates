"""Handler for fetch an IP address from NLB ENIs.

When creating a AWS::ElasticLoadBalancingV2::LoadBalancer with Type=network,
to have a restrictive IP Security Group, the static private IP address of
the ENIs attached to the Load Balancer are required. Unfortunately,
CloudFormation does not have a !GetAtt for this value. The lookup takes
it's place.

Example:

    lookups:
      elbv2_ip: path.to.local_lookups.handle

    stacks:
      nlb-stack:
        class_path: ...
      stack-name:
        class_path: ...
        variables:
          NlbIpAddresses: ${elbv2_ip ${rxref nlb-stack::LoadBalancerFullName}}

"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from stacker.session_cache import get_session


def handle(value, provider=None, context=None, **kwargs):
    """Fetch an IP address from NLB ENIs.

    Arguments:
        value {str} -- full name of an elbv2 load balancer
        provider {:class:`stacker.provider.base.BaseProvider`} --
            subclass of the base provider
        context {:class:`stacker.context.Context`} -- stacker context

    Returns:
        str -- comma delimited list of IP addresses

    """
    if provider is None:
        raise ValueError('Provider is required')
    if context is None:
        raise ValueError('Context is required')

    session = get_session(provider.region)
    client = session.client('ec2')

    response = client.describe_network_interfaces(
        Filters=[{
            'Name': 'description',
            'Values': ['ELB {}'.format(value)]
        }]
    )

    ip_addresses = [
        address['PrivateIpAddress'] for addresses in
        map(
            lambda i: i['PrivateIpAddresses'],
            response['NetworkInterfaces']
        )
        for address in addresses
    ]

    return ip_addresses
