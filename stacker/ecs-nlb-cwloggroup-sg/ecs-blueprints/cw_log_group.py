#!/usr/bin/env python
"""Stacker module for creating a standalone CW Log Group."""
#from utils import standalone_output

from troposphere import (
    GetAtt, Join, Output, Ref, Sub, Export, ec2, Tags, logs
)
from troposphere import elasticloadbalancingv2 as alb

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


class CWLogGroup(Blueprint):
    """Extends Stacker Blueprint class."""

    VARIABLES = {
        'LogGroupName': {
            'type': CFNString,
            'description': 'What is the log group name'
        },
        
    }

    def add_log_group(self):
        """Add Log Group to template."""
        template = self.template
        variables = self.get_variables()

        CloudWatchLogGroup = template.add_resource(
            logs.LogGroup(
                variables['LogGroupName'].value,
                LogGroupName="/ecs/{}".format(variables['LogGroupName'].value),
                RetentionInDays=3653
            )
        )


    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        template.add_version('2010-09-09')
        template.add_description(
            "Onica - CW Log Group - (1.0.0)"
        )
        self.add_log_group()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    print(CWLogGroup('test',
                                  Context({"namespace": "test"}),
                                  None).to_json()
    )
