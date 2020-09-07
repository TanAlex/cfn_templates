#!/usr/bin/env python
"""Module with Cloudwatch Alarms."""
from __future__ import print_function
from os.path import dirname, realpath
import sys

from troposphere import Equals, If, Not, Ref, cloudwatch

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNCommaDelimitedList, CFNString


class CwAlarm(Blueprint):
    """Stacker blueprint for creating CloudWatch alarms."""

    VARIABLES = {
        'AlarmDescription': {
            'type': CFNString,
            'default': '',
            'description': 'Alarm description'
        },
        'AlarmName': {
            'type': CFNString,
            'default': '',
            'description': 'Name to assign to CloudWatch alarm (leave blank '
                           'to automatically assign it)'
        },
        'AlarmThreshold': {
            'type': CFNString,
            'default': '0',
            'description': 'Expression for the rule to be scheduled'
        },
        'EvaluationPeriods': {
            'type': CFNString,
            'default': '3',
            'description': 'Number of periods over which data is compared to '
                           'the specified threshold'
        },
        'AlertTopicArn': {
            'type': CFNCommaDelimitedList,
            'description': 'A list of the SNS topics to which alarm actions '
                           'will be associated'
        },
        'ComparisonOperator': {
            'type': CFNString,
            'default': 'GreaterThanThreshold',
            'description': 'The arithmetic operation to use when comparing '
                           'the specified Statistic and Threshold',
            'allowed_values': ['GreaterThanOrEqualToThreshold',
                               'GreaterThanThreshold',
                               'LessThanThreshold',
                               'LessThanOrEqualToThreshold']
        },
        'DimensionName': {
            'type': CFNString,
            'default': '',
            'description': 'Name of the metric dimension'
        },
        'DimensionValue': {
            'type': CFNString,
            'default': '',
            'description': 'Value representing the dimension measurement'
        },
        'MetricName': {
            'type': CFNString,
            'default': '',
            'description': 'The metric to alert on'
        },
        'Namespace': {
            'type': CFNString,
            'default': 'Sturdy Lambda Checks',
            'description': 'Metric namespace'
        },
        'Statistic': {
            'type': CFNString,
            'default': 'Sum',
            'description': 'The statistic to apply to the alarm\'s '
                           'associated metric',
            'allowed_values': ['SampleCount',
                               'Average',
                               'Sum',
                               'Minimum',
                               'Maximum']
        },
        'StatisticPeriod': {
            'type': CFNString,
            'default': '300',
            'description': 'The time over which the specified statistic (e.g. '
                           'sum) is applied (the CFN parameter "Period"). '
                           'Specify time in seconds, in multiples of 60'
        },
        'TreatMissingData': {
            'type': CFNString,
            'default': '',
            'description': 'Specify "breaching" to trigger alarm on missing '
                           'data'
        }
    }

    def add_conditions(self):
        """Set up template conditions."""
        template = self.template
        variables = self.get_variables()

        template.add_condition(
            'AlarmDescriptionSpecified',
            Not(Equals(variables['AlarmDescription'].ref, ''))
        )

        template.add_condition(
            'AlarmNameSpecified',
            Not(Equals(variables['AlarmName'].ref, ''))
        )

        template.add_condition(
            'MetricDimensionSpecified',
            Not(Equals(variables['DimensionName'].ref, ''))
        )

        template.add_condition(
            'TreatMissingDataSpecified',
            Not(Equals(variables['TreatMissingData'].ref, ''))
        )

    def add_resources(self):
        """Add resources to template."""
        template = self.template
        variables = self.get_variables()

        template.add_resource(
            cloudwatch.Alarm(
                'Alarm',
                AlarmDescription=If(
                    'AlarmDescriptionSpecified',
                    variables['AlarmDescription'].ref,
                    Ref('AWS::NoValue')
                ),
                AlarmName=If(
                    'AlarmNameSpecified',
                    variables['AlarmName'].ref,
                    Ref('AWS::NoValue')
                ),
                Namespace=variables['Namespace'].ref,
                Statistic=variables['Statistic'].ref,
                Period=variables['StatisticPeriod'].ref,
                EvaluationPeriods=variables['EvaluationPeriods'].ref,
                Threshold=variables['AlarmThreshold'].ref,
                AlarmActions=variables['AlertTopicArn'].ref,
                OKActions=variables['AlertTopicArn'].ref,
                ComparisonOperator=variables['ComparisonOperator'].ref,
                Dimensions=If(
                    'MetricDimensionSpecified',
                    [cloudwatch.MetricDimension(
                        Name=variables['DimensionName'].ref,
                        Value=variables['DimensionValue'].ref)],
                    Ref('AWS::NoValue')),
                MetricName=variables['MetricName'].ref,
                TreatMissingData=If(
                    'TreatMissingDataSpecified',
                    variables['TreatMissingData'].ref,
                    Ref('AWS::NoValue')
                )
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.add_version('2010-09-09')
        self.template.add_description("Sturdy Platform - Core - CloudWatch "
                                      " Alarm - {0}".format(version()))
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

    print(CwAlarm('test',
                  Context({'namespace': 'test'}),
                  None).to_json())
