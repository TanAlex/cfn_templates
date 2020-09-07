"""Finds the latest AMI for a given platform."""

import re
import logging
import sys
import boto3

LOGGER = logging.getLogger(__name__)
# Set to DEBUG to see details in lambda logs; ERROR for production
LOGGER.setLevel('ERROR')
UBUNTUPATTERN = re.compile(r"^ubuntu-([0-9]{2,2})\.([0-9]{2,2})$")


def describe_images(platform, region):
    """Determine AMI filters."""
    ami_filters = [
        {'Name': 'architecture', 'Values': ['x86_64']},
        {'Name': 'is-public', 'Values': ['true']},
        {'Name': 'root-device-type', 'Values': ['ebs']},
        {'Name': 'state', 'Values': ['available']},
        {'Name': 'virtualization-type', 'Values': ['hvm']}
    ]
    ami_owners = []

    # Using naming conventions from
    # https://github.com/test-kitchen/kitchen-ec2/tree/master/lib/kitchen/driver/aws/standard_platform
    if platform == 'centos-7':
        ami_filters.extend([
            {'Name': 'owner-id', 'Values': ['679593333241']},
            {'Name': 'product-code', 'Values': ['aw0evgkw8e5c1q413zgy5pjce']}
        ])
        ami_owners = ['aws-marketplace']
    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/walkthrough-custom-resources-lambda-lookup-amiids.html
    elif platform == 'amazon-hvm64':
        ami_filters.extend([
            {'Name': 'name', 'Values': ['amzn-ami-hvm*x86_64-gp2']}
        ])
        ami_owners = ['amazon']
    elif UBUNTUPATTERN.match(platform):
        i = UBUNTUPATTERN.match(platform)
        ami_filters.extend([
            {'Name': 'name',
             'Values': ['ubuntu/images/*/ubuntu-*-%s.%s*' % (i.groups()[0],
                                                             i.groups()[1])]},
            {'Name': 'owner-id', 'Values': ['099720109477']}
        ])
    elif platform in ['windows-2012r2', 'windows-2016']:
        win_filter = [{'Name': 'owner-alias', 'Values': ['amazon']}]
        if platform == 'windows-2012r2':
            win_filter.append(
                {'Name': 'name',
                 'Values': ['Windows_Server-2012-R2_RTM-English-*-Base-*',
                            'Windows_Server-2012-R2_SP*-English-*-Base-*']}
            )
        elif platform == 'windows-2016':
            win_filter.append(
                {'Name': 'name',
                 'Values': ['Windows_Server-2016-English-Full-Base-*']}
            )
        ami_filters.extend(win_filter)
    else:
        LOGGER.error('Platform %s not supported', platform)
        ami_filters = []

    if ami_filters is not []:
        client = boto3.client('ec2', region_name=region)

        return client.describe_images(
            ExecutableUsers=['all'],  # public images
            Owners=ami_owners,
            Filters=ami_filters
        )
    else:
        return {'ResponseMetadata': 'Invalid platform provided'}


def handler(event, context):
    """Lambda entry point."""
    if event.get('ResourceProperties'):  # Invoked as CFN custom resource
        import cfnresponse  # pylint: disable=import-error
        # Bypass all execution when the 'resource' is being deleted
        if event['RequestType'] == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {}, False)
            return True
        region = event['ResourceProperties']['Region']
        platform = event['ResourceProperties']['Platform']
    else:  # invoked directly
        region = event['Region']
        platform = event['Platform']

    describe_response = describe_images(platform, region)

    response_data = {}
    if 'Images' in describe_response and describe_response['Images'] != []:
        # Get ami from last dict in the list of matching Images
        sorted_images = sorted(describe_response['Images'],
                               key=lambda k: k['Name'])
        latest_ami = sorted_images[-1]
        if platform.startswith('amazon-'):
            # Ensure rc images aren't included
            for i in reversed(sorted_images):
                if '.rc-' in latest_ami['Name']:
                    latest_ami = i
        response_data['ImageId'] = latest_ami['ImageId']
        response_data['Name'] = latest_ami['Name']
        if 'cfnresponse' in sys.modules:
            response_code = cfnresponse.SUCCESS
    elif 'cfnresponse' in sys.modules:
        response_code = cfnresponse.FAILED
        response_data['Data'] = describe_response['ResponseMetadata']

    LOGGER.info('Returning response data: %s', str(response_data))
    if 'cfnresponse' in sys.modules:
        cfnresponse.send(event, context, response_code, response_data, False)
    else:
        return response_data
