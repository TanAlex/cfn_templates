#!/usr/bin/env python
"""Stacker module for creating an ECS Task."""


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



class ECSTask(Blueprint):
    """Extend Stacker Blueprint class."""

    VARIABLES = {
        'ContainerName':{
            'type': CFNString
        },
        'Image': {
            'type': CFNString
        },
        'TaskName': {
            'type': CFNString,
            'description': 'URL to set as the upstream',
            'default': 'test'
        },
        'PortMappings': {
            'type': TroposphereType(ecs.PortMapping, many=True)
        }
    }

    def add_ecs_task(self):
        """Adds ECS Task to template"""
        template = self.template
        variables = self.get_variables()

        EcsTaskExecutionRole = template.add_resource(
            iam.Role(
                'EcsTaskExecutionRole',
                Path='/',
                ManagedPolicyArns=[
                    'arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy',
                    # TODO: GET RID OF THE BELOW
                    'arn:aws:iam::aws:policy/AmazonS3FullAccess'
                ],
                AssumeRolePolicyDocument={'Version': '2012-10-17',
                                        'Statement': [{'Action': 'sts:AssumeRole',
                                                        'Principal':
                                                        {'Service': 'ecs-tasks.amazonaws.com'},
                                                        'Effect': 'Allow',
                                                        }]}
            )
        )


        Task = template.add_resource(
            ecs.TaskDefinition(
                variables['TaskName'].value,
                NetworkMode='awsvpc',
                TaskRoleArn=Ref(EcsTaskExecutionRole),
                ContainerDefinitions=[
                    ecs.ContainerDefinition(
                        Image=variables['Image'].ref,
                        Name=variables['ContainerName'].ref,
                        Memory=1536,
                        MemoryReservation=500,
                        LogConfiguration=ecs.LogConfiguration(
                            LogDriver='awslogs',
                            Options={
                                "awslogs-group": "/ecs/{}".format(variables['TaskName'].value),
                                "awslogs-region": Ref('AWS::Region'),
                                "awslogs-stream-prefix": "ecs"
                            }
                        ),
                        PortMappings=variables['PortMappings']
                    )
                ]
            )
        )

        

        

        template.add_output(Output(
            'TaskDefinitionARN',
            Description='ECS Task ARN',
            Value=Ref(Task),
        ))

    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        template.add_version('2010-09-09')
        template.add_description(
            "Onica - ECS Task - (1.0.0)"
        )
        self.add_ecs_task()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context
    print (ECSTask(
        'test', Context({"namespace": "test"})
    ).to_json())
