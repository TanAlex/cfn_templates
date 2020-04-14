#!/usr/bin/env python
"""Stacker module for creating an ECS Service."""


from troposphere import (
    And, Equals, If, Join, Not, Output, Ref, autoscaling, ec2, iam, AWSHelperFn, Base64, ecs
)
from troposphere.autoscaling import MetricsCollection
from troposphere.policies import (
    UpdatePolicy, AutoScalingRollingUpdate  # , AutoScalingReplacingUpdate
)

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import TroposphereType
import awacs.ec2
import awacs.s3
import awacs.ssm
import awacs.sts
import json
from awacs.aws import Allow, Policy, Principal, Statement
# Linter is incorrectly flagging the automatically generated functions in awacs
from awacs.aws import StringEquals, StringLike  # noqa pylint: disable=no-name-in-module

from stacker.blueprints.variables.types import (
    CFNCommaDelimitedList, CFNNumber, CFNString, EC2SecurityGroupIdList,
    EC2SubnetIdList
)

from stacker.lookups.handlers.file import parameterized_codec


class ECSService(Blueprint):
    """Extend Stacker Blueprint class."""

    VARIABLES = {

        'ServiceName': {
            'type': CFNString,
            'description': 'URL to set as the upstream',
            'default': 'test'
        },
        'TaskDefinitionARN': {
            'type': CFNString
        },
        'ClusterName': {
            'type': CFNString
        },
        'ECSLoadBalancers': {
            'type': TroposphereType(ecs.LoadBalancer, many=True)
        },
        'DesiredCount': {
            'type': CFNNumber
        },
        'SecurityGroups':{
            'type': EC2SecurityGroupIdList
        },
        'Subnets':{
            'type': EC2SubnetIdList
        }
    }

    def add_ecs_service(self):
        """Adds ECS Service to template"""
        template = self.template
        variables = self.get_variables()

        Service = template.add_resource(
            ecs.Service(
                variables['ServiceName'].value,
                Cluster=variables['ClusterName'].ref,
                DesiredCount=variables['DesiredCount'].ref,
                LaunchType='EC2',
                LoadBalancers=variables['ECSLoadBalancers'],
                # Role=Ref(ecsServiceRole),
                NetworkConfiguration=ecs.NetworkConfiguration(
                    AwsvpcConfiguration=ecs.AwsvpcConfiguration(
                        SecurityGroups=variables['SecurityGroups'].ref,
                        Subnets=variables['Subnets'].ref
                    )
                ),
                TaskDefinition=variables['TaskDefinitionARN'].ref
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        template.add_version('2010-09-09')
        template.add_description(
            "Onica - ECS Service - (1.0.0)"
        )
        self.add_ecs_service()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context
    print(ECSService(
        'test', Context({"namespace": "test"})
    ).to_json())
