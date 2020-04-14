#!/usr/bin/env python
"""Stacker module for creating a standalone SG."""
#from utils import standalone_output

from troposphere import (
    GetAtt, Join, Output, Ref, Sub, Export, ec2, Tags
)
from troposphere import elasticloadbalancingv2 as alb

import awacs.ec2
import awacs.s3
import awacs.ssm
import awacs.sts
from awacs.aws import Allow, Condition, Policy, Principal, Statement
# Linter is incorrectly flagging the automatically generated functions in awacs
from awacs.aws import StringEquals, StringLike  # noqa pylint: disable=no-name-in-module
from stacker.blueprints.variables.types import TroposphereType
from stacker.blueprints.base import Blueprint, resolve_variable
from stacker.blueprints.variables.types import (
    CFNCommaDelimitedList, CFNNumber, CFNString, EC2SecurityGroupIdList,
    EC2SubnetIdList
)


class ECSSecurityGroups(Blueprint):
    """Extends Stacker Blueprint class."""

    VARIABLES = {
        'VpcId': {
            'type': CFNString,
            'description': 'What VPC is this being deployed to?'
        },
        'EnvironmentName': {
            'type': CFNString,
            'description': 'Name of Environment',
            'default': 'common'
        },
        'Ingress':{
            'type': TroposphereType(ec2.SecurityGroupRule, many=True)
        },
        'NlbIps':{
            'type': list
        }
    }

    def add_security_groups(self):
        """Add SG to template."""
        template = self.template
        variables = self.get_variables()

        ECSInstanceSG = template.add_resource(
            ec2.SecurityGroup(
                'ECSInstanceSG',
                GroupName=Join('-',['ECSInstanceSG', variables['EnvironmentName'].ref]),
                GroupDescription='The security group for ECS-EC2 instances',
                VpcId=variables['VpcId'].ref,
                SecurityGroupIngress=variables['Ingress'],
            )
        )
        for i, ip in enumerate(variables['NlbIps']):
            template.add_resource(
                ec2.SecurityGroupIngress(
                    f'NLBIPIngress{i}',
                    GroupId=Ref(ECSInstanceSG),
                    FromPort=0,
                    ToPort=65535,
                    CidrIp=ip+'/32',
                    Description='Allowing NLB access',
                    IpProtocol='tcp'
                )
            )

        template.add_output(Output(
            "{}Name".format(ECSInstanceSG.title),
            Description='SG Name',
            Value=Ref(ECSInstanceSG)
        ))


    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        template.add_version('2010-09-09')
        template.add_description(
            "Onica - SG - (1.0.0)"
        )
        self.add_security_groups()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    standalone_output.json(
        blueprint=ECSSecurityGroups('test',
                                  Context({"namespace": "test"}),
                                  None)
    )
