"""SSM Parameter Document."""
from __future__ import print_function

from troposphere import (
    AWSHelperFn, ssm, Ref
)

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString

__version__ = '1.0.0'

TEMPLATE_DESCRIPTION = 'Onica - SSM Parameter Document - {}'.format(
    __version__
)


class BlueprintClass(Blueprint):
    """Blueprint for creating ssm parameter."""

    VARIABLES = {
        'ApplicationName': {
            'type': CFNString,
        },
        'CustomerName': {
            'type': CFNString,
            'default': ''
        },
        'EnvironmentName': {
            'type': CFNString,
            'description': 'Name of Environment',
            'default': 'common'
        },
        'LogGroupName': {
            'type': CFNString,
            'description': 'CloudWatch log group name for CW Agent to log to',
            'default': 'MyCWLogGroupName'
        },
        'ParameterName': {
            'type': CFNString
        },
        'ParameterValue': {
            'type': AWSHelperFn,
            'description': 'Content of SSM::Parameter',
            'default': Ref('AWS::NoValue')
        },
    }

    def create_template(self):
        """Create the template."""
        template = self.template
        variables = self.get_variables()
        template.add_version('2010-09-09')
        template.add_description(TEMPLATE_DESCRIPTION)

        try:
            if variables['ParameterValue'] == Ref('AWS::NoValue'):
                value = self.context.hook_data['metrics'][
                    variables['ParameterName'].value
                ]
            else:
                value = variables['ParameterValue']

        except KeyError:
            value = {'', ''}

        template.add_resource(ssm.Parameter(
            'SsmDocument',
            Name=variables['ParameterName'].ref,
            Type='String',
            Value=value
        ))


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    print(BlueprintClass('test', Context({'namespace': 'test'})), 'DummyValue')
