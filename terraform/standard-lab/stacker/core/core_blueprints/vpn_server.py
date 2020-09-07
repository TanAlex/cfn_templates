#!/usr/bin/env python
"""Load dependencies."""
from __future__ import print_function
from os import path
from os.path import dirname, realpath
import sys

from troposphere import (
    AWSHelperFn, And, Base64, Equals, GetAtt, If, ImportValue, Join, Not, Or,
    Ref, Sub, autoscaling, awslambda, cloudformation, ec2, iam
)

import awacs.autoscaling
import awacs.ec2
import awacs.awslambda
import awacs.logs
import awacs.s3
import awacs.sns
from awacs.helpers.trust import make_simple_assume_policy
from awacs.aws import Allow, Condition, PolicyDocument, Statement
# Linter is incorrectly flagging the automatically generated functions in awacs
from awacs.aws import StringLike  # pylint: disable=no-name-in-module

from stacker.lookups.handlers.file import parameterized_codec
from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import (
    CFNCommaDelimitedList, CFNString, EC2SecurityGroupIdList, EC2VPCId
)

AWS_LAMBDA_DIR = path.join(path.dirname(path.realpath(__file__)),
                           'aws_lambda')
IAM_ARN_PREFIX = 'arn:aws:iam::aws:policy/service-role/'
AZS = 3


def get_str_class():
    """Return string class for the running version of python."""
    if sys.version_info[0] == 2:
        return basestring
    return str


class AMIId(cloudformation.AWSCustomObject):
    """Class for AMI lookup custom resource."""

    resource_type = "Custom::AMIId"

    props = {
        'ServiceToken': (get_str_class(), True),
        'Platform': (get_str_class(), True),
        'Region': (get_str_class(), True)
    }


class SubnetLookup(cloudformation.AWSCustomObject):
    """Class for subnet lookup custom resource."""

    resource_type = "Custom::SubnetLookup"

    props = {
        'ServiceToken': (get_str_class(), True),
        'CoreVPCStack': (get_str_class(), True),
        'Region': (get_str_class(), True)
    }


class VpnServer(Blueprint):
    """Blueprint for setting up Sturdy Networks core AWS environment."""

    subnet_lookup_src = parameterized_codec(
        open(path.join(AWS_LAMBDA_DIR, 'subnet_lookup.py'), 'r').read(),
        False  # disable base64 encoding
    )

    VARIABLES = {
        'SubnetLookupLambdaFunction': {'type': AWSHelperFn,
                                       'description': 'Lambda function code',
                                       'default': subnet_lookup_src},
        'AMILookupArn': {'type': CFNString,
                         'description': 'ARN of the Lambda function providing '
                                        'AMI ids; unused if a value is '
                                        'provided for the "VPNAMI" parameter.',
                         'default': ''},
        # Not using EC2KeyPairKeyName to allow KeyName to be optional
        'KeyName': {'type': CFNString,
                    'description': 'Name of an existing EC2-VPC KeyPair',
                    'default': ''},
        'BucketKey': {'type': CFNString,
                      'description': 'S3 prefix for chef cookbook archives '
                                     'and artifacts. The environment name '
                                     'will be prepended to this. E.g. if '
                                     '"ChefBucketName" is "foo", '
                                     '"BucketKey" is "bar", '
                                     '"EnvironmentName" is "dev", and '
                                     '"ChefDataBucketName" is "citadel", '
                                     'instances will pull configuration '
                                     'tarballs from s3://foo/dev/bar/ and be '
                                     'able to access files (e.g. secrets/'
                                     'artifacts) in s3://citadel/dev/bar/',
                      'default': 'vpnservers'},
        'ChefBucketName': {'type': CFNString,
                           'description': 'Name of bucket storing core Chef '
                                          'configuration',
                           'default': 'common'},
        'ChefDataBucketName': {'type': CFNString,
                               'description': 'Name of bucket storing extra '
                                              'Chef data',
                               'default': 'citadel'},
        'CustomerName': {'type': CFNString,
                         'description': 'The nickname for the new customer. '
                                        'Must be all lowercase letters, '
                                        'should not contain spaces or special '
                                        'characters, nor should it include '
                                        'any part of EnvironmentName.',
                         'allowed_pattern': '[-_ a-z]*',
                         'default': ''},
        'EnvironmentName': {'type': CFNString,
                            'description': 'Name of Environment',
                            'default': 'common'},
        'VpcCidr': {'type': CFNString,
                    'description': 'VPC CIDR block (required for creating NAT '
                                   'security group rules for NATing traffic).',
                    'default': '10.12.0.0/21'},
        'CoreVPCStack': {'type': CFNString,
                         'description': 'Core VPC CFN stack name (used to '
                                        'lookup subnets).'},
        # Not using EC2ImageId to allow VPNAMI to be optional
        'VPNAMI': {'type': CFNString,
                   'description': 'AMI ID for VPN instance (leave blank to '
                                  ' use the "VPNOS" parameter)',
                   'default': ''},
        'VPNManagedPolicies': {'type': CFNCommaDelimitedList,
                               'description': 'Managed policy ARNs to apply '
                                              'to the VPN instances.'},
        'VPNOS': {'type': CFNString,
                  'description': 'OS to deploy on the VPN server (can be '
                                 'overridden with the "VPNAMI" parameter). '
                                 'Also used to determine instance userdata '
                                 'configuration (i.e. yum vs apt package '
                                 'management).',
                  'default': 'ubuntu-16.04',
                  'allowed_values': ['centos-7', 'ubuntu-16.04', '']},
        'VpnEipPublicIp': {'type': CFNString,
                           'description': 'Elastic IP for the VPN Instance'},
        'ManagementInstanceType': {'type': CFNString,
                                   'description': 'Type of the management '
                                                  'instances. T2 not allowed '
                                                  'in dedicated tenancy.',
                                   'default': 'm3.medium'},
        'VPNSecurityGroups': {'type': EC2SecurityGroupIdList,
                              'description': 'Security groups to apply to the '
                                             'VPN instances.'},
        'VpcId': {'type': EC2VPCId,
                  'description': 'VPC id.'},
        'VpcInstanceTenancy': {'type': CFNString,
                               'description': 'Tenancy of the VPC',
                               'default': 'dedicated',
                               'allowed_values': [
                                   'dedicated',
                                   'default'
                               ]},
        'VPNSubnet': {'type': CFNString,
                      'description': 'Address range for a VPN subnet.',
                      'default': '10.12.14.0/24'},
        'ChefClientVersion': {'type': CFNString,
                              'description': 'Version of chef-client to '
                                             'install.',
                              'default': '12.19.36'},
        'PublicRouteTable': {'type': CFNString,
                             'description': '(typically unused) Public route '
                                            'table id.',
                             'default': ''},
        'PublicSubnets': {'type': CFNCommaDelimitedList,
                          'description': '(typically unused) Public subnets '
                                         'in which to deploy the VPN server.',
                          'default': ''},
        'PrivateRouteTable1': {'type': CFNString,
                               'description': '(typically unused) Private '
                                              'route table 1 id.',
                               'default': ''},
        'PrivateRouteTable2': {'type': CFNString,
                               'description': '(typically unused) Private '
                                              'route table 2 id.',
                               'default': ''},
        'PrivateRouteTable3': {'type': CFNString,
                               'description': '(typically unused) Private '
                                              'route table 3 id.',
                               'default': ''},
        'PrivateSubnetCount': {'type': CFNString,
                               'description': 'Optional number of private '
                                              'subnets to reference in VPC '
                                              'stack. Leave at 0 to look this '
                                              'up dynamically via Lambda.',
                               'default': '0'},
        'ChefRunList': {'type': CFNString,
                        'description': 'Optional override for the Chef recipe '
                                       'name; leave blank to default to '
                                       '"recipe[CUSTOMERNAME_vpn]".',
                        'default': ''}
    }

    def add_conditions(self):
        """Set up template conditions."""
        template = self.template
        variables = self.get_variables()

        template.add_condition(
            'SSHKeySpecified',
            And(Not(Equals(variables['KeyName'].ref, '')),
                Not(Equals(variables['KeyName'].ref, 'undefined')))
        )
        template.add_condition(
            'MissingVPNAMI',
            Or(Equals(variables['VPNAMI'].ref, ''),
               Equals(variables['VPNAMI'].ref, 'undefined'))
        )
        template.add_condition(
            'RHELUserData',
            Not(Equals(variables['VPNOS'].ref, 'ubuntu-16.04'))
        )
        template.add_condition(
            'ChefRunListSpecified',
            And(Not(Equals(variables['ChefRunList'].ref, '')),
                Not(Equals(variables['ChefRunList'].ref, 'undefined')))
        )
        template.add_condition(
            'PublicRouteTableSpecified',
            And(Not(Equals(variables['PublicRouteTable'].ref, '')),
                Not(Equals(variables['PublicRouteTable'].ref, 'undefined')))
        )
        template.add_condition(
            'PublicSubnetsOmitted',
            Equals(Join('', variables['PublicSubnets'].ref), '')
        )
        for i in range(AZS):
            template.add_condition(
                '%iPrivateSubnetsCreated' % (i + 1),
                Equals(variables['PrivateSubnetCount'].ref, str(i + 1))
            )
        template.add_condition(
            'PrivateSubnetCountOmitted',
            Equals(variables['PrivateSubnetCount'].ref, '0')
        )

    def add_resources(self):
        """Add resources to template."""
        template = self.template
        variables = self.get_variables()

        vpnrole = template.add_resource(
            iam.Role(
                'VPNRole',
                AssumeRolePolicyDocument=make_simple_assume_policy(
                    'ec2.amazonaws.com'
                ),
                ManagedPolicyArns=variables['VPNManagedPolicies'].ref,
                Path='/',
                Policies=[
                    iam.Policy(
                        PolicyName=Join('-', ['customer-vpn-server-role',
                                              variables['EnvironmentName'].ref,
                                              variables['CustomerName'].ref]),
                        PolicyDocument=PolicyDocument(
                            Version='2012-10-17',
                            Statement=[
                                # ModifyInstanceAttribute is for src/dst check
                                Statement(
                                    Action=[awacs.ec2.DescribeRouteTables,
                                            awacs.ec2.DescribeAddresses,
                                            awacs.ec2.AssociateAddress,
                                            awacs.ec2.CreateRoute,
                                            awacs.ec2.ReplaceRoute,
                                            awacs.ec2.ModifyInstanceAttribute],
                                    Effect=Allow,
                                    Resource=['*']
                                ),
                                Statement(
                                    Action=[awacs.aws.Action('s3', 'Get*'),
                                            awacs.aws.Action('s3', 'List*'),
                                            awacs.aws.Action('s3', 'Put*')],
                                    Effect=Allow,
                                    Resource=[
                                        Join('',
                                             ['arn:aws:s3:::',
                                              variables['ChefDataBucketName'].ref,  # noqa pylint: disable=line-too-long
                                              '/',
                                              variables['EnvironmentName'].ref,
                                              '/',
                                              variables['BucketKey'].ref,
                                              '/*'])
                                    ]
                                ),
                                Statement(
                                    Action=[awacs.s3.ListBucket],
                                    Effect=Allow,
                                    Resource=[
                                        Join('',
                                             ['arn:aws:s3:::',
                                              variables['ChefDataBucketName'].ref])  # noqa pylint: disable=line-too-long
                                    ],
                                    Condition=Condition(
                                        StringLike('s3:prefix',
                                                   [Join('',
                                                         [variables['EnvironmentName'].ref,  # noqa pylint: disable=line-too-long
                                                          '/',
                                                          variables['BucketKey'].ref,  # noqa pylint: disable=line-too-long
                                                          '/*'])
                                                   ])
                                    )
                                )
                            ]
                        )
                    )
                ]
            )
        )
        vpninstanceprofile = template.add_resource(
            iam.InstanceProfile(
                'VPNInstanceProfile',
                Path='/',
                Roles=[Ref(vpnrole)]
            )
        )

        amiid = template.add_resource(
            AMIId(
                'AMIId',
                Condition='MissingVPNAMI',
                Platform=variables['VPNOS'].ref,
                Region=Ref('AWS::Region'),
                ServiceToken=variables['AMILookupArn'].ref
            )
        )

        # Lookup subnets from core VPC stack
        subnetlookuplambdarole = template.add_resource(
            iam.Role(
                'SubnetLookupLambdaRole',
                Condition='PrivateSubnetCountOmitted',
                AssumeRolePolicyDocument=make_simple_assume_policy(
                    'lambda.amazonaws.com'
                ),
                ManagedPolicyArns=[
                    IAM_ARN_PREFIX + 'AWSLambdaBasicExecutionRole'
                ],
                Policies=[
                    iam.Policy(
                        PolicyName=Join('-', ['subnetlookup-lambda-role',
                                              variables['EnvironmentName'].ref,
                                              variables['CustomerName'].ref]),
                        PolicyDocument=PolicyDocument(
                            Version='2012-10-17',
                            Statement=[
                                Statement(
                                    Action=[awacs.aws.Action('cloudformation',
                                                             'DescribeStack*'),
                                            awacs.aws.Action('cloudformation',
                                                             'Get*')],
                                    Effect=Allow,
                                    Resource=[
                                        Join('',
                                             ['arn:aws:cloudformation:',
                                              Ref('AWS::Region'),
                                              ':',
                                              Ref('AWS::AccountId'),
                                              ':stack/',
                                              variables['CoreVPCStack'].ref,
                                              '/*'])
                                    ]
                                )
                            ]
                        )
                    )
                ]
            )
        )

        cfncustomresourcesubnetlookup = template.add_resource(
            awslambda.Function(
                'CFNCustomResourceSubnetLookup',
                Condition='PrivateSubnetCountOmitted',
                Description='Find subnets created by core stack',
                Code=awslambda.Code(
                    ZipFile=variables['SubnetLookupLambdaFunction']
                ),
                Handler='index.handler',
                Role=GetAtt(subnetlookuplambdarole, 'Arn'),
                Runtime='python2.7',
                Timeout=10
            )
        )

        subnetlookup = template.add_resource(
            SubnetLookup(
                'SubnetLookup',
                Condition='PrivateSubnetCountOmitted',
                CoreVPCStack=variables['CoreVPCStack'].ref,
                Region=Ref('AWS::Region'),
                ServiceToken=GetAtt(cfncustomresourcesubnetlookup, 'Arn')
            )
        )

        common_userdata_prefix = [
            "#cloud-config\n",
            "package_update: true\n",
            "package_upgrade: false\n",
            "write_files:\n",
            "  - path: /usr/local/bin/update_vpn_routes.sh\n",
            "    permissions: '0755'\n",
            "    content: |\n",
            "      #!/bin/bash\n",
            "      \n",
            "      export AWS_DEFAULT_REGION=\"",
            Ref('AWS::Region'),
            "\"\n",
            "      my_instance_id=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)\n",  # noqa pylint: disable=line-too-long
            "      \n",
            "      publicroutetableid=",
            If('PrivateSubnetCountOmitted',
               GetAtt(subnetlookup.title, 'PublicRouteTableId'),
               If('PublicRouteTableSpecified',
                  variables['PublicRouteTable'].ref,
                  ImportValue(Sub("${%s}-PublicRouteTable" % variables['CoreVPCStack'].name)))),  # noqa pylint: disable=line-too-long
            "\n",
            "      private_route_tables=(",
            If('PrivateSubnetCountOmitted',
               GetAtt(subnetlookup.title, 'PrivateRouteTables'),
               If('3PrivateSubnetsCreated',
                  If('PublicRouteTableSpecified',
                     Join(' ',
                          [variables['PrivateRouteTable1'].ref,
                           variables['PrivateRouteTable2'].ref,
                           variables['PrivateRouteTable3'].ref]),
                     Join(' ',
                          [ImportValue(Sub("${%s}-PrivateRouteTable1" % variables['CoreVPCStack'].name)),  # noqa pylint: disable=line-too-long
                           ImportValue(Sub("${%s}-PrivateRouteTable2" % variables['CoreVPCStack'].name)),  # noqa pylint: disable=line-too-long
                           ImportValue(Sub("${%s}-PrivateRouteTable3" % variables['CoreVPCStack'].name))])),  # noqa pylint: disable=line-too-long
                  If('2PrivateSubnetsCreated',
                     If('PublicRouteTableSpecified',
                        Join(' ',
                             [variables['PrivateRouteTable1'].ref,
                              variables['PrivateRouteTable2'].ref]),
                        Join(' ',
                             [ImportValue(Sub("${%s}-PrivateRouteTable1" % variables['CoreVPCStack'].name)),  # noqa pylint: disable=line-too-long
                              ImportValue(Sub("${%s}-PrivateRouteTable2" % variables['CoreVPCStack'].name))])),  # noqa pylint: disable=line-too-long,
                     If('PublicRouteTableSpecified',
                        variables['PrivateRouteTable1'].ref,
                        ImportValue(Sub("${%s}-PrivateRouteTable1" % variables['CoreVPCStack'].name)))))),  # noqa pylint: disable=line-too-long
            ")\n",
            "\n",
            "      openvpnroutepubdest=",
            variables['VPNSubnet'].ref,
            "\n",
            "      \n",
            "      # Disabling sourceDestCheck\n",
            "      aws ec2 modify-instance-attribute --instance-id ${my_instance_id} --source-dest-check \"{\\\"Value\\\": false}\"\n",  # noqa pylint: disable=line-too-long
            "      \n",
            "      if aws ec2 describe-route-tables | grep ${openvpnroutepubdest}; then\n",  # noqa pylint: disable=line-too-long
            "          # Update 'OpenVPNRoutePub' to point to this instance\n",  # noqa pylint: disable=line-too-long
            "          aws ec2 replace-route --route-table-id ${publicroutetableid} --destination-cidr-block ${openvpnroutepubdest} --instance-id ${my_instance_id}\n",  # noqa pylint: disable=line-too-long
            "          # Update private routes\n",
            "          for i in \"${private_route_tables[@]}\"\n",
            "          do\n",
            "              aws ec2 replace-route --route-table-id $i --destination-cidr-block ${openvpnroutepubdest} --instance-id ${my_instance_id}\n",  # noqa pylint: disable=line-too-long
            "          done\n",
            "      else\n",
            "          # Create 'OpenVPNRoutePub'\n",
            "          aws ec2 create-route --route-table-id ${publicroutetableid} --destination-cidr-block ${openvpnroutepubdest} --instance-id ${my_instance_id}\n",  # noqa pylint: disable=line-too-long
            "          # Create private routes\n",
            "          for i in \"${private_route_tables[@]}\"\n",
            "          do\n",
            "              aws ec2 create-route --route-table-id $i --destination-cidr-block ${openvpnroutepubdest} --instance-id ${my_instance_id}\n",  # noqa pylint: disable=line-too-long
            "          done\n",
            "      fi\n",
            "      \n",
            "\n",
            "  - path: /etc/chef/sync_cookbooks.sh\n",
            "    permissions: '0755'\n",
            "    owner: 'root'\n",
            "    group: 'root'\n",
            "    content: |\n",
            "      #!/bin/bash\n",
            "      set -e -o pipefail\n",
            "      \n",
            "      aws --region ",
            Ref('AWS::Region'),
            " s3 sync s3://",
            variables['ChefBucketName'].ref,
            "/",
            variables['EnvironmentName'].ref,
            "/",
            variables['BucketKey'].ref,
            "/ /etc/chef/\n",
            "      if compgen -G \"/etc/chef/cookbooks-*.tar.gz\" > /dev/null; then\n",  # noqa pylint: disable=line-too-long
            "          echo \"Cookbook archive found.\"\n",
            "          if [ -d \"/etc/chef/cookbooks\" ]; then\n",
            "              echo \"Removing previously extracted cookbooks.\"\n",  # noqa pylint: disable=line-too-long
            "              rm -r /etc/chef/cookbooks\n",
            "          fi\n",
            "          echo \"Extracting highest numbered cookbook archive.\"\n",  # noqa pylint: disable=line-too-long
            "          cbarchives=(/etc/chef/cookbooks-*.tar.gz)\n",
            "          tar -zxf \"${cbarchives[@]: -1}\" -C /etc/chef\n",
            "          chown -R root:root /etc/chef\n",
            "      fi\n",
            "      \n",
            "\n",
            "  - path: /etc/chef/perform_chef_run.sh\n",
            "    permissions: '0755'\n",
            "    owner: 'root'\n",
            "    group: 'root'\n",
            "    content: |\n",
            "      #!/bin/bash\n",
            "      set -e -o pipefail\n",
            "      \n",
            "      chef-client -z -r '",
            If('ChefRunListSpecified',
               variables['ChefRunList'].ref,
               Join('', ['recipe[',
                         variables['CustomerName'].ref,
                         '_vpn]'])),
            "' -c /etc/chef/client.rb -E ",
            variables['EnvironmentName'].ref,
            " --force-formatter --no-color -F min\n",
            "\n",
            "  - path: /etc/chef/client.rb\n",
            "    permissions: '0644'\n",
            "    owner: 'root'\n",
            "    group: 'root'\n",
            "    content: |\n",
            "      log_level :info\n",
            "      log_location '/var/log/chef/client.log'\n",
            "      ssl_verify_mode :verify_none\n",
            "      cookbook_path '/etc/chef/cookbooks'\n",
            "      node_path '/etc/chef/nodes'\n",
            "      role_path '/etc/chef/roles'\n",
            "      data_bag_path '/etc/chef/data_bags'\n",
            "      environment_path '/etc/chef/environments'\n",
            "      local_mode 'true'\n",
            "\n",
            "  - path: /etc/chef/environments/",
            variables['EnvironmentName'].ref,
            ".json\n",
            "    permissions: '0644'\n",
            "    owner: 'root'\n",
            "    group: 'root'\n",
            "    content: |\n",
            "      {\n",
            "        \"name\": \"",
            variables['EnvironmentName'].ref,
            "\",\n",
            "        \"default_attributes\": {\n",
            "          \"sturdy\": {\n",
            "            \"openvpn\": {\n",
            "              \"core_vpc_cidr\": \"",
            variables['VpcCidr'].ref,
            "\",\n",
            "              \"vpn_elastic_ip\": \"",
            variables['VpnEipPublicIp'].ref,
            "\",\n",
            "              \"vpn_subnet_cidr\": \"",
            variables['VPNSubnet'].ref,
            "\",\n",
            "              \"chef_data_bucket_name\": \"",
            variables['ChefDataBucketName'].ref,
            "\",\n",
            "              \"chef_data_bucket_folder\": \"",
            variables['EnvironmentName'].ref,
            "/",
            variables['BucketKey'].ref,
            "\",\n",
            "              \"chef_data_bucket_region\": \"",
            Ref('AWS::Region'),
            "\"\n",
            "            }\n",
            "          }\n",
            "        },\n",
            "        \"json_class\": \"Chef::Environment\",\n",
            "        \"description\": \"",
            variables['EnvironmentName'].ref,
            " environment\",\n",
            "        \"chef_type\": \"environment\"\n",
            "      }\n",
            "\n",
            "runcmd:\n",
            "  - set -euf\n",
            "  - echo 'Attaching EIP'\n",
            "  - pip install aws-ec2-assign-elastic-ip\n",
            # Allowing this command to fail (with ||true) as sturdy_openvpn
            # 2.3.0+ can handle this association instead. This will be removed
            # entirely in the next major release of this module (at which time
            # use of the updated sturdy_openvpn cookbook will be required)
            "  - aws-ec2-assign-elastic-ip --region ",
            Ref('AWS::Region'),
            " --valid-ips ",
            variables['VpnEipPublicIp'].ref,
            " || true\n",
            "  - echo 'Updating Routes'\n",
            "  - /usr/local/bin/update_vpn_routes.sh\n",
            "  - echo 'Installing Chef'\n",
            "  - curl --max-time 10 --retry-delay 5 --retry 5 -L https://www.chef.io/chef/install.sh | bash -s -- -v ",  # noqa pylint: disable=line-too-long
            variables['ChefClientVersion'].ref,
            "\n",
            "  - echo 'Configuring Chef'\n",
            "  - mkdir -p /var/log/chef /etc/chef/data_bags /etc/chef/nodes /etc/chef/roles\n",  # noqa pylint: disable=line-too-long
            "  - chmod 0755 /etc/chef\n",
            "  - /etc/chef/sync_cookbooks.sh\n",
            "  - /etc/chef/perform_chef_run.sh\n"
        ]

        vpnserverlaunchconfig = template.add_resource(
            autoscaling.LaunchConfiguration(
                'VpnServerLaunchConfig',
                AssociatePublicIpAddress=True,
                BlockDeviceMappings=[
                    # CentOS AMIs don't include this by default
                    ec2.BlockDeviceMapping(
                        DeviceName='/dev/sda1',
                        Ebs=ec2.EBSBlockDevice(
                            DeleteOnTermination=True
                        )
                    )
                ],
                IamInstanceProfile=Ref(vpninstanceprofile),
                ImageId=If(
                    'MissingVPNAMI',
                    GetAtt(amiid, 'ImageId'),
                    variables['VPNAMI'].ref),
                InstanceType=variables['ManagementInstanceType'].ref,
                InstanceMonitoring=False,  # extra granularity not worth cost
                KeyName=If('SSHKeySpecified',
                           variables['KeyName'].ref,
                           Ref('AWS::NoValue')),
                PlacementTenancy=variables['VpcInstanceTenancy'].ref,
                SecurityGroups=variables['VPNSecurityGroups'].ref,
                UserData=If(
                    'RHELUserData',
                    Base64(Join('', common_userdata_prefix + [
                        "yum_repos:\n",
                        "  epel:\n",
                        "    name: Extra Packages for $releasever - $basearch\n",  # noqa pylint: disable=line-too-long
                        "    baseurl: http://download.fedoraproject.org/pub/epel/7/$basearch\n",  # noqa pylint: disable=line-too-long
                        "    enabled: true\n",
                        "    failovermethod: priority\n",
                        "    gpgcheck: true\n",
                        "    gpgkey: https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-7\n",  # noqa pylint: disable=line-too-long
                        "packages:\n",
                        "  - awscli\n",
                        "  - python-pip\n",
                        "  - python2-boto\n",
                        "  - python2-boto3\n"
                    ])),
                    Base64(Join('', common_userdata_prefix + [
                        "packages:\n",
                        "  - awscli\n",
                        "  - python-pip\n",
                        "  - python-boto\n",
                        "  - python-boto3\n"
                    ]))
                )
            )
        )

        template.add_resource(
            autoscaling.AutoScalingGroup(
                'VPNServerASG',
                MinSize=1,
                MaxSize=1,
                LaunchConfigurationName=Ref(vpnserverlaunchconfig),
                Tags=[
                    autoscaling.Tag('Name',
                                    Join('-',
                                         [variables['CustomerName'].ref,
                                          'vpn',
                                          variables['EnvironmentName'].ref]),
                                    True),
                    autoscaling.Tag('environment',
                                    variables['EnvironmentName'].ref,
                                    True),
                    autoscaling.Tag('customer',
                                    variables['CustomerName'].ref,
                                    True)
                ],
                VPCZoneIdentifier=If('PublicSubnetsOmitted',
                                     GetAtt(subnetlookup.title,
                                            'PublicSubnetList'),
                                     variables['PublicSubnets'].ref)
            )
        )

    def create_template(self):
        """Boilerplate for CFN Template."""
        self.template.add_version('2010-09-09')
        self.template.add_description("Sturdy Platform - Core - VPN Server "
                                      "- {0}".format(version()))
        self.add_conditions()
        self.add_resources()


def version():
    """Call version function from top of repo."""
    root_dir = dirname(dirname(dirname(dirname(realpath(__file__)))))
    if root_dir not in sys.path:
        sys.path.append(root_dir)
    import platform_version  # pylint: disable=import-error
    return platform_version.version()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    print(VpnServer('test',
                    Context({'namespace': 'test'}),
                    None).to_json())
