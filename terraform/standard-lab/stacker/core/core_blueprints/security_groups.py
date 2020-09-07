#!/usr/bin/env python
"""Module with VPC security groups."""
from __future__ import print_function
from os.path import dirname, realpath
import sys

from troposphere import Export, Join, Output, Ref, Sub, Tags, ec2

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString, EC2VPCId


class SecurityGroups(Blueprint):
    """Stacker blueprint for core AWS environment security groups."""

    VARIABLES = {
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
        'VpcId': {'type': EC2VPCId,
                  'description': 'VPC id.'}
    }

    def add_resources(self):
        """Add resources to template."""
        template = self.template
        variables = self.get_variables()

        vpnsecuritygroup = template.add_resource(
            ec2.SecurityGroup(
                'VPNSecurityGroup',
                GroupDescription=Join('-', [variables['CustomerName'].ref,
                                            'vpn-servers']),
                SecurityGroupIngress=[
                    ec2.SecurityGroupRule(
                        IpProtocol='udp',
                        FromPort='1194',  # OpenVPN server
                        ToPort='1194',
                        CidrIp='0.0.0.0/0')
                ],
                SecurityGroupEgress=[
                    ec2.SecurityGroupRule(
                        IpProtocol='-1',
                        FromPort='0',
                        ToPort='65535',
                        CidrIp='0.0.0.0/0')
                ],
                Tags=Tags(
                    Name=Join(
                        '-',
                        [variables['CustomerName'].ref,
                         'vpn-servers',
                         variables['EnvironmentName'].ref]
                    )
                ),
                VpcId=Ref('VpcId')
            )
        )
        template.add_output(
            Output(
                vpnsecuritygroup.title,
                Description='Security group for VPN servers',
                Export=Export(
                    Sub('${AWS::StackName}-%s' % vpnsecuritygroup.title)
                ),
                Value=Ref(vpnsecuritygroup)
            )
        )

        allsecuritygroup = template.add_resource(
            ec2.SecurityGroup(
                'AllSecurityGroup',
                GroupDescription=Join('-', [variables['CustomerName'].ref,
                                            'all-servers']),
                SecurityGroupIngress=[
                    ec2.SecurityGroupRule(
                        IpProtocol='-1',
                        FromPort='0',
                        ToPort='65535',
                        SourceSecurityGroupId=Ref(vpnsecuritygroup))
                ],
                SecurityGroupEgress=[
                    ec2.SecurityGroupRule(
                        IpProtocol='-1',
                        FromPort='0',
                        ToPort='65535',
                        CidrIp='0.0.0.0/0')
                ],
                Tags=Tags(
                    Name=Join(
                        '-',
                        [variables['CustomerName'].ref,
                         'all-servers',
                         variables['EnvironmentName'].ref]
                    )
                ),
                VpcId=Ref('VpcId')
            )
        )
        template.add_output(
            Output(
                allsecuritygroup.title,
                Description='Security group for all servers',
                Export=Export(
                    Sub('${AWS::StackName}-%s' % allsecuritygroup.title)
                ),
                Value=Ref(allsecuritygroup)
            )
        )

        internalsecuritygroup = template.add_resource(
            ec2.SecurityGroup(
                'InternalSecurityGroup',
                GroupDescription=Join('-', [variables['CustomerName'].ref,
                                            'internal-servers']),
                SecurityGroupIngress=[],
                SecurityGroupEgress=[
                    ec2.SecurityGroupRule(
                        IpProtocol='-1',
                        FromPort='0',
                        ToPort='65535',
                        CidrIp='0.0.0.0/0')
                ],
                Tags=Tags(
                    Name=Join(
                        '-',
                        [variables['CustomerName'].ref,
                         'internal-servers',
                         variables['EnvironmentName'].ref]
                    )
                ),
                VpcId=Ref('VpcId')
            )
        )
        template.add_output(
            Output(
                internalsecuritygroup.title,
                Description='Security group for internal servers',
                Export=Export(
                    Sub('${AWS::StackName}-%s' % internalsecuritygroup.title)
                ),
                Value=Ref(internalsecuritygroup)
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.add_version('2010-09-09')
        self.template.add_description("Sturdy Platform - Core - Security "
                                      "Groups - {0}".format(version()))
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

    print(SecurityGroups('test',
                         Context({'namespace': 'test'}),
                         None).to_json())
