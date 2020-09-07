#!/usr/bin/env python
"""Module with VPC and related resources."""
from __future__ import print_function
from os.path import dirname, realpath
import sys

from troposphere import (
    Equals, Export, GetAtt, GetAZs, Join, Not, Output, Ref, Select, Sub, Tags,
    ec2, And, Condition
)

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString

AZS = 2


class Vpc(Blueprint):
    """Blueprint for setting up Sturdy Networks core AWS environment."""

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
        'VpcCidr': {'type': CFNString,
                    'description': 'VPC CIDR block (required for creating NAT '
                                   'security group rules for NATing traffic).',
                    'default': '10.12.0.0/21'},
        'VpcInstanceTenancy': {'type': CFNString,
                               'description': 'Tenancy of the VPC',
                               'default': 'dedicated',
                               'allowed_values': [
                                   'dedicated',
                                   'default'
                               ]},
        'AzOffset': {'type': int,
                     'description': 'Off set for Availability Zones',
                     'default': 0}
    }

    # Subnet parameters are mostly identical; dynamically build them here
    for i in range(AZS):
        VARIABLES['PublicSubnet%i' % (i + 1)] = {
            'type': CFNString,
            'description': 'Address range for a public subnet.',
            'default': '10.12.%i.0/24' % i
        }
        VARIABLES['PrivateSubnet%i' % (i + 1)] = {
            'type': CFNString,
            'description': 'Address range for a private subnet.',
            'default': '10.12.%i.0/24' % (i + AZS)
        }

    def add_conditions(self):
        """Set up AZ conditions."""
        template = self.template
        for i in range(AZS):
            template.add_condition(
                'PublicAZ%i' % (i + 1),
                Not(Equals(Ref('PublicSubnet%i' % (i + 1)), ''))
            )
            template.add_condition(
                'PrivateAZ%i' % (i + 1),
                Not(Equals(Ref('PrivateSubnet%i' % (i + 1)), ''))
            )
            template.add_condition(
                'CreateNATGateway%i' % (i + 1),
                And(Condition('PublicAZ%i' % (i + 1)),
                    Condition('PrivateAZ%i' % (i + 1)))
            )

    def add_resources(self):
        """Add resources to template."""
        template = self.template
        variables = self.get_variables()

        # Add StackName to outputs (for ease of reference by child stacks)
        template.add_output(
            Output(
                'StackName',
                Description='Name of this CloudFormation stack',
                Value=Ref('AWS::StackName')
            )
        )

        vpc = template.add_resource(
            ec2.VPC(
                'VPC',
                CidrBlock=variables['VpcCidr'].ref,
                EnableDnsSupport=True,
                EnableDnsHostnames=True,
                InstanceTenancy=variables['VpcInstanceTenancy'].ref,
                Tags=Tags(
                    Application=Ref('AWS::StackName'),
                    Name=Join(
                        '-',
                        [variables['CustomerName'].ref,
                         'vpc',
                         variables['EnvironmentName'].ref]
                    ),
                    Network='Public'
                )
            )
        )
        template.add_output(
            Output(
                'VPC',
                Description='VPC',
                Export=Export(Sub('${AWS::StackName}-VPC')),
                Value=Ref(vpc)
            )
        )
        template.add_output(
            Output(
                'CidrBlock',
                Description='Set of IP addresses for the VPC',
                Export=Export(Sub('${AWS::StackName}-CidrBlock')),
                Value=GetAtt(vpc, 'CidrBlock')
            )
        )

        # Create subnets
        for i in range(AZS):
            for zone in ['Public', 'Private']:
                template.add_resource(
                    ec2.Subnet(
                        '%sSubnet%s' % (zone[:3], str(i + 1)),
                        Condition='%sAZ%i' % (zone, (i + 1)),
                        VpcId=Ref(vpc),
                        AvailabilityZone=Select(
                            str(i + variables['AzOffset']),
                            GetAZs('')),
                        CidrBlock=Ref('%sSubnet%s' % (zone, str(i + 1))),
                        Tags=Tags(
                            Application=Ref('AWS::StackName'),
                            Name=Join(
                                '-',
                                [variables['CustomerName'].ref,
                                 zone.lower(),
                                 variables['EnvironmentName'].ref,
                                 Select(
                                     str(i + variables['AzOffset']),
                                     GetAZs(''))]
                            ),
                            Network='%s - %s' % (zone, str(i + 1))
                        )
                    )
                )
                template.add_output(
                    Output(
                        '%sSubnet%s' % (zone[:3], str(i + 1)),
                        Condition='%sAZ%s' % (zone, str(i + 1)),
                        Description='%sSubnet%s' % (zone[:3], str(i + 1)),
                        Export=Export(
                            Sub('${AWS::StackName}-'
                                '%sSubnet%s' % (zone[:3], str(i + 1)))
                        ),
                        Value=Ref('%sSubnet%s' % (zone[:3], str(i + 1)))
                    )
                )
                template.add_output(
                    Output(
                        '%sSubnet%sAZ' % (zone[:3], str(i + 1)),
                        Condition='%sAZ%s' % (zone, str(i + 1)),
                        Description='%sSubnet%s Availability Zone' % (zone[:3],
                                                                      str(i + 1)),  # noqa
                        Export=Export(
                            Sub('${AWS::StackName}-'
                                '%sSubnet%sAZ' % (zone[:3], str(i + 1)))
                        ),
                        Value=GetAtt('%sSubnet%s' % (zone[:3], str(i + 1)),
                                     'AvailabilityZone')
                    )
                )

        internetgateway = template.add_resource(
            ec2.InternetGateway(
                'InternetGateway',
                Tags=Tags(
                    Application=Ref('AWS::StackName'),
                    Name=Join(
                        '-',
                        [variables['CustomerName'].ref,
                         'igw',
                         variables['EnvironmentName'].ref]
                    ),
                    Network='Public'
                )
            )
        )
        template.add_resource(
            ec2.VPCGatewayAttachment(
                'GatewayToInternet',
                InternetGatewayId=Ref(internetgateway),
                VpcId=Ref(vpc),
            )
        )

        # Elastic IPs
        for i in range(AZS):
            template.add_resource(
                ec2.EIP(
                    'NAT%iElasticIP' % (i + 1),
                    Condition='CreateNATGateway%i' % (i + 1),
                    Domain='vpc'
                )
            )
            template.add_output(
                Output(
                    'NAT%iElasticIP' % (i + 1),
                    Condition='CreateNATGateway%i' % (i + 1),
                    Description='Elastic IP for NATs %i' % (i + 1),
                    Export=Export(
                        Sub('${AWS::StackName}-NAT%iElasticIP' % (i + 1))
                    ),
                    Value=Ref('NAT%iElasticIP' % (i + 1)),
                )
            )

        # NAT Gateways
        for i in range(AZS):
            template.add_resource(
                ec2.NatGateway(
                    'NATGateway%i' % (i + 1),
                    Condition='CreateNATGateway%i' % (i + 1),
                    AllocationId=GetAtt('NAT%iElasticIP' % (i + 1),
                                        'AllocationId'),
                    SubnetId=Ref('PubSubnet%i' % (i + 1))
                )
            )

        # Route tables
        publicroutetable = template.add_resource(
            ec2.RouteTable(
                'PublicRouteTable',
                VpcId=Ref(vpc),
                Tags=Tags(
                    Application=Ref('AWS::StackName'),
                    Name=Join(
                        '-',
                        [variables['CustomerName'].ref,
                         'public-routes',
                         variables['EnvironmentName'].ref]
                    ),
                    Network='Public'
                )
            )
        )
        template.add_output(
            Output(
                publicroutetable.title,
                Description=publicroutetable.title,
                Export=Export(
                    Sub('${AWS::StackName}-%s' % publicroutetable.title)
                ),
                Value=Ref(publicroutetable)
            )
        )
        for i in range(AZS):
            template.add_resource(
                ec2.RouteTable(
                    'PrivateRouteTable%i' % (i + 1),
                    Condition='PrivateAZ%i' % (i + 1),
                    VpcId=Ref(vpc),
                    Tags=Tags(
                        Application=Ref('AWS::StackName'),
                        Name=Join(
                            '-',
                            [variables['CustomerName'].ref,
                             'private-routes',
                             variables['EnvironmentName'].ref,
                             Select(
                                 str(i + variables['AzOffset']),
                                 GetAZs(''))]
                        ),
                        Network='Private - %i' % (i + 1)
                    )
                )
            )
            template.add_output(
                Output(
                    'PrivateRouteTable%i' % (i + 1),
                    Condition='PrivateAZ%i' % (i + 1),
                    Description='PrivateRouteTable%i' % (i + 1),
                    Export=Export(Sub('${AWS::StackName}-'
                                      'PrivateRouteTable%i' % (i + 1))),
                    Value=Ref('PrivateRouteTable%i' % (i + 1))
                )
            )

        # Routes & Route Table Associations
        template.add_resource(
            ec2.Route(
                'PublicRoute',
                DestinationCidrBlock='0.0.0.0/0',
                GatewayId=Ref(internetgateway),
                RouteTableId=Ref(publicroutetable)
            )
        )

        for i in range(AZS):
            template.add_resource(
                ec2.Route(
                    'PrivateRoute%i' % (i + 1),
                    Condition='CreateNATGateway%i' % (i + 1),
                    DestinationCidrBlock='0.0.0.0/0',
                    NatGatewayId=Ref('NATGateway%i' % (i + 1)),
                    RouteTableId=Ref('PrivateRouteTable%i' % (i + 1))
                )
            )

            template.add_resource(
                ec2.SubnetRouteTableAssociation(
                    'PubSubnet%iRTAssoc' % (i + 1),
                    Condition='PublicAZ%i' % (i + 1),
                    RouteTableId=Ref(publicroutetable),
                    SubnetId=Ref('PubSubnet%i' % (i + 1))
                )
            )
            template.add_resource(
                ec2.SubnetRouteTableAssociation(
                    'PriSubnet%iRTAssoc' % (i + 1),
                    Condition='PrivateAZ%i' % (i + 1),
                    RouteTableId=Ref('PrivateRouteTable%i' % (i + 1)),
                    SubnetId=Ref('PriSubnet%i' % (i + 1))
                )
            )

    def create_template(self):
        """Boilerplate for CFN Template."""
        self.template.add_version('2010-09-09')
        self.template.add_description("Sturdy Platform - Core - VPC "
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

    print(Vpc('test',
              Context({'namespace': 'test'}),
              None).to_json())
