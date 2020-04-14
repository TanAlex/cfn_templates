#!/usr/bin/env python
"""Stacker module for creating a Squid NLB."""

from troposphere import (
    GetAtt, Join, Output, Ref, Sub, Export, ec2, Tags
)
from modules.squid_server.module_version import version
from troposphere import elasticloadbalancingv2 as nlb

# Linter is incorrectly flagging the automatically generated functions in awacs
from awacs.aws import StringEquals, StringLike  # noqa pylint: disable=no-name-in-module

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import (
    CFNCommaDelimitedList, CFNString
)

TEMPLATE_DESCRIPTION = 'Squid Network Load Balancer - {}'.format(version())


class NetworkLoadBalancer(Blueprint):
    """Extends Stacker Blueprint class."""

    VARIABLES = {
        'ApplicationName': {
            'type': CFNString,
            'description': 'Instance name tag value (will have "CustomerName" '
                           'prepended and "EnvironmentName" appended to it)',
            'default': 'application'
        },
        'CustomerName': {
            'type': CFNString,
            'description': 'The nickname for the customer/tenant. Must be all'
                           ' lowercase letters, should not contain spaces or '
                           'special characters, nor should it include any part'
                           ' of EnvironmentName',
            'allowed_pattern': '[-_ a-z]*',
            'default': 'undefined'
        },
        'EnvironmentName': {
            'type': CFNString,
            'description': 'Name of Environment',
            'default': 'common'
        },
        'Scheme': {
            'type': CFNString,
            'description': 'NLB Scheme (internet-facing or internal)',
            'default': 'internet-facing',
            'allowed_values': [
                'internet-facing',
                'internal'
            ]
        },
        'CrossZoneEnabled': {
            'type': CFNString,
            'description': 'Enable Cross Zone Loadbalancing',
            'default': 'true'
        },
        'LoadBalancerSubnets': {
            'type': CFNCommaDelimitedList,
            'description': 'Subnets in which the NLB will be deployed',
            'default': ''
        },
        'VpcId': {
            'type': CFNString,
            'description': 'What VPC is this being deployed to?'
        },
        'SubnetMappings': {
            'type': str,
            'description': 'subent mappings',
            'default': ''
        },
        'CostCenter': {
            'type': CFNString,
            'description': 'Tag value.',
            'default': '0'
        },
        'TechOwner': {
            'type': CFNString,
            'description': 'Tag value.',
            'default': 'Onica'
        },
        'TechOwnerEmail': {
            'type': CFNString,
            'description': 'Tag value.',
            'default': 'incidents@onica.com'
        },
        'DataClassification': {
            'type': CFNString,
            'description': 'Data Classification level',
            'default': 'none',
            'allowed_values': [
                'none',
                'sensitive',
                'regulated',
                'sensitive_regulated'
            ]
        }
    }

    def add_nlb(self):
        """Add NLB to template."""
        template = self.template
        variables = self.get_variables()

        subnet_mappings = []
        subnet_filtered = list(filter(None,
                                      variables['SubnetMappings'].split(',')))
        for i, subnet in enumerate(subnet_filtered):

            eip = template.add_resource(
                ec2.EIP(
                    'EIP{}'.format(i),
                    Domain='vpc',
                    DeletionPolicy='Retain'
                )
            )
            template.add_output(Output(
                'EIPValue{}'.format(i),
                Description='EIP ID',
                Export=Export(Sub('${AWS::StackName}-%s-ip' % eip.title)),
                Value=Ref(eip)
            ))
            template.add_output(Output(
                'EIPAllocID{}'.format(i),
                Description='EIP ID',
                Export=Export(Sub('${AWS::StackName}-%s-allocId' % eip.title)),
                Value=GetAtt(eip, 'AllocationId')
            ))

            subnet_mappings.append(
                nlb.SubnetMapping(
                    'SubnetMapping{}'.format(i),
                    AllocationId=GetAtt(eip, 'AllocationId'),
                    SubnetId=subnet
                )
            )
        n_lb = nlb.LoadBalancer(
            'NLB{}'.format(
                variables['Scheme'].value.replace('-', '').replace('_', '')),
            Name=Join('-', [variables['CustomerName'].ref,
                            'squid',
                            'nlb',
                            variables['EnvironmentName'].ref]),
            Tags=Tags(
                Company=variables['CustomerName'].ref,
                Application=variables['ApplicationName'].ref,
                Environment=variables['EnvironmentName'].ref,
                CostCenter=variables['CostCenter'].ref,
                TechOwner=variables['TechOwner'].ref,
                TechOwnerEmail=variables['TechOwnerEmail'].ref,
                DataClassification=variables['DataClassification'].ref

            ),
            LoadBalancerAttributes=[
                nlb.LoadBalancerAttributes(
                    Key='load_balancing.cross_zone.enabled',
                    Value='true'
                )
            ],
            Scheme=variables['Scheme'].ref,
            Type='network'
        )
        if subnet_mappings:
            n_lb.SubnetMappings = subnet_mappings
        if variables['LoadBalancerSubnets'].value:
            n_lb.Subnets = variables['LoadBalancerSubnets'].ref
            n_lb.Name = Join('-', [variables['CustomerName'].ref,
                                   'squid',
                                   'nlb',
                                   variables['EnvironmentName'].ref,
                                   'Internal'])
        network_lb = template.add_resource(n_lb)

        template.add_output(Output(
            '{}Arn'.format(network_lb.title),
            Description='Load Balancer Arn',
            Export=Export(Sub('${AWS::StackName}-%s-ARN' % network_lb.title)),
            Value=Ref(network_lb)
        ))
        template.add_output(Output(
            '{}DnsName'.format(network_lb.title),
            Description='Load Balancer DNSName',
            Export=Export(
                Sub('${AWS::StackName}-%s-DNSName' % network_lb.title)),
            Value=GetAtt(network_lb, 'DNSName')
        ))
        template.add_output(Output(
            '{}FullName'.format(network_lb.title),
            Description='Load Balancer FullName',
            Export=Export(
                Sub('${AWS::StackName}-%s-FullName' % network_lb.title)),
            Value=GetAtt(network_lb, 'LoadBalancerFullName')
        ))
        # HTTP/TCP Target Groups and Listeners
        ports = [3128]
        for port in ports:
            app_tg = template.add_resource(
                nlb.TargetGroup(
                    'TargetGroup%s' % port,
                    Port=port,
                    Protocol='TCP',
                    Tags=Tags(
                        Company=variables['CustomerName'].ref,
                        Application=variables['ApplicationName'].ref,
                        Environment=variables['EnvironmentName'].ref,
                        CostCenter=variables['CostCenter'].ref,
                        TechOwner=variables['TechOwner'].ref,
                        TechOwnerEmail=variables['TechOwnerEmail'].ref,
                        DataClassification=variables['DataClassification'].ref

                    ),
                    VpcId=variables['VpcId'].ref
                )
            )
            template.add_output(Output(
                '{}Name'.format(app_tg.title),
                Description='Name',
                Value=GetAtt(app_tg, 'TargetGroupName')
            ))
            template.add_output(Output(
                '{}FullName'.format(app_tg.title),
                Description='Target Group FullName',
                Value=GetAtt(app_tg, 'TargetGroupFullName')
            ))
            template.add_output(Output(
                '{}Arn'.format(app_tg.title),
                Description='Target Group Arn',
                Export=Export(Sub('${AWS::StackName}-%s' % app_tg.title)),
                Value=Ref(app_tg)
            ))

            template.add_resource(
                nlb.Listener(
                    'NlbListener%s' % port,
                    DefaultActions=[
                        nlb.Action(
                            TargetGroupArn=Ref(app_tg),
                            Type='forward'
                        )
                    ],
                    LoadBalancerArn=Ref(network_lb),
                    Port=port,
                    Protocol='TCP'
                )
            )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        template.set_version('2010-09-09')
        template.set_description(TEMPLATE_DESCRIPTION)
        self.add_nlb()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context
    print(NetworkLoadBalancer('test',
                              Context({"namespace": "test"})).to_json()
          )
