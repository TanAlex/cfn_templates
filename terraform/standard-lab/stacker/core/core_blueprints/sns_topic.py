#!/usr/bin/env python
"""Module with SNS alert topic."""
from __future__ import print_function
from os.path import dirname, realpath
import sys

from troposphere import Ref, Output, sns

from stacker.blueprints.base import Blueprint


class SnsTopic(Blueprint):
    """Blueprint for setting up SNS topic."""

    VARIABLES = {}

    def add_resources(self):
        """Add resources to template."""
        template = self.template

        pagerdutyalert = template.add_resource(
            sns.Topic(
                'Topic'
            )
        )

        template.add_output(
            Output(
                "%sARN" % pagerdutyalert.title,
                Description='SNS topic',
                Value=Ref(pagerdutyalert)
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.add_version('2010-09-09')
        self.template.add_description("Sturdy Platform - Core - SNS Topic "
                                      "- {0}".format(version()))
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

    print(SnsTopic('test',
                   Context({'namespace': 'test'}),
                   None).to_json())
