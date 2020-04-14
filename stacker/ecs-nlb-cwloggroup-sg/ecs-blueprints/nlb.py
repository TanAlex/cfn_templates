#!/usr/bin/env python
"""Stacker module for creating a NLB."""
# from utils import standalone_output

from troposphere import (
    GetAtt, Join, Output, Ref, Sub, Export, ec2, Tags
)
from troposphere import elasticloadbalancingv2 as nlb

import awacs.ec2
import awacs.s3
import awacs.ssm
import awacs.sts
from awacs.aws import Allow, Condition, Policy, Principal, Statement
# Linter is incorrectly flagging the automatically generated functions in awacs
from awacs.aws import StringEquals, StringLike  # noqa pylint: disable=no-name-in-module

from stacker.blueprints.base import Blueprint, resolve_variable
from stacker.blueprints.variables.types import (
    CFNCommaDelimitedList, CFNNumber, CFNString, EC2SecurityGroupIdList,
    EC2SubnetIdList
)


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
            'default': ''
        },
        'EnvironmentName': {
            'type': CFNString,
            'description': 'Name of Environment',
            'default': 'common'
        },
        'CrossZoneEnabled': {
            'type': CFNString,
            'description': 'Enable Cross Zone Loadbalancing',
            'default': 'true'
        },
        'HealthCheckProtocol': {
            'type': CFNString,
            'description': 'That proto should the health check use',
            'default': 'HTTP'
        },
        'HealthCheckPort': {
            'type': CFNString,
            'description': 'That port should the health check use',
            'default': '80'
        },
        'AppSubnets': {
            'type': EC2SubnetIdList,
            'description': 'Subnets in which the NLB will be deployed'
        },
        'VpcId': {
            'type': CFNString,
            'description': 'What VPC is this being deployed to?'
        },
        'PortList': {
            'type': list
        }
    }

    def add_nlb(self):
        """Add NLB to template."""
        template = self.template
        variables = self.get_variables()

        nlb_lb = template.add_resource(
            nlb.LoadBalancer(
                'Nlb',
                Name=Sub(
                    '${CustomerName}-${ApplicationName}-nlb-${EnvironmentName}'),
                Scheme='internal',
                Subnets=variables['AppSubnets'].ref,
                LoadBalancerAttributes=[
                    nlb.LoadBalancerAttributes(
                        Key='load_balancing.cross_zone.enabled',
                        Value='true'
                    )
                ],
                Tags=[
                    ec2.Tag(
                        'Name',
                        Join('-', [variables['CustomerName'].ref,
                                   variables['ApplicationName'].ref,
                                   variables['EnvironmentName'].ref])),
                    ec2.Tag('CustomerName',
                            variables['CustomerName'].ref),
                    ec2.Tag('ApplicationName',
                            variables['ApplicationName'].ref),
                    ec2.Tag('EnvironmentName',
                            variables['EnvironmentName'].ref)
                ],
                Type='network'
            )
        )
        template.add_output(Output(
            '{}Arn'.format(nlb_lb.title),
            Description='Network Load Balancer Arn',
            Value=Ref(nlb_lb)
        ))
        template.add_output(Output(
            '{}DnsName'.format(nlb_lb.title),
            Description='Network Load Balancer DNSName',
            Value=GetAtt(nlb_lb, 'DNSName')
        ))
        template.add_output(Output(
            '{}Name'.format(nlb_lb.title),
            Description='Network Load Balancer Name',
            Value=GetAtt(nlb_lb, 'LoadBalancerName')
        ))
        template.add_output(Output(
            '{}LoadBalancerFullName'.format(nlb_lb.title),
            Description='Network Load Balancer LoadBalancerFullName',
            Value=GetAtt(nlb_lb, 'LoadBalancerFullName')
        ))

        # TODO: Parametrize this
        ports = variables['PortList']
        for port in ports:
            nlb_tg = template.add_resource(
                nlb.TargetGroup(
                    'TargetGroup%s' % port,
                    Name=Join('-', [variables['ApplicationName'].ref,
                                    port,
                                    variables['EnvironmentName'].ref]),
                    Port=port,
                    Protocol='TCP',
                    Tags=Tags(
                        Port=port,
                        Name=Join('-', [variables['ApplicationName'].ref,
                                        port,
                                        variables['EnvironmentName'].ref]),
                        CustomerName=variables['CustomerName'].ref,
                        ApplicationName=variables['ApplicationName'].ref,
                        EnvironmentName=variables['EnvironmentName'].ref
                    ),
                    HealthyThresholdCount=3,
                    UnhealthyThresholdCount=3,
                    TargetType='ip',
                    TargetGroupAttributes=[
                        nlb.TargetGroupAttribute(
                            Key='deregistration_delay.timeout_seconds',
                            Value='15'
                        )
                    ],
                    VpcId=variables['VpcId'].ref
                )
            )
            template.add_output(Output(
                '{}Name'.format(nlb_tg.title),
                Description='Name',
                Value=GetAtt(nlb_tg, 'TargetGroupName')
            ))
            template.add_output(Output(
                '{}FullName'.format(nlb_tg.title),
                Description='Target Group FullName',
                Value=GetAtt(nlb_tg, 'TargetGroupFullName')
            ))
            template.add_output(Output(
                '{}Arn'.format(nlb_tg.title),
                Description='Target Group Arn',
                Export=Export(Sub('${AWS::StackName}-%s' % nlb_tg.title)),
                Value=Ref(nlb_tg)
            ))
            listener = template.add_resource(
                nlb.Listener(
                    'NlbListener%s' % port,
                    DefaultActions=[
                        nlb.Action(
                            TargetGroupArn=Ref(nlb_tg),
                            Type='forward'
                        )
                    ],
                    LoadBalancerArn=Ref(nlb_lb),
                    Port=port,
                    Protocol='TCP'
                )
            )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        template.add_version('2010-09-09')
        template.add_description(
            "Onica - NLB - (1.0.0)"
        )
        self.add_nlb()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    print(NetworkLoadBalancer('test',
                          Context({"namespace": "test"}),
                          None).to_json()
          )
