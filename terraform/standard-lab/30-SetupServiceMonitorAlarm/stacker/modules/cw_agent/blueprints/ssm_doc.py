"""SSM RunCommand Document."""
from __future__ import print_function

from troposphere import (
    AWSProperty,AWSHelperFn, ssm, Ref,Export, Output, Sub
)


from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString

__version__ = '1.0.0'

TEMPLATE_DESCRIPTION = 'Onica - SSM RunCommand Document - {}'.format(
    __version__
)


class BlueprintClass(Blueprint):
    """Blueprint for creating lambda function."""

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
        'DocumentName': {
            'type': CFNString
        },
        'DocumentContent': {
            'type': AWSHelperFn,
            'description': 'Content of SSM::Document',
            'default': Ref('AWS::NoValue')
        },
        'S3BucketName': {
            'type': CFNString,
            'description': 'The S3 Bucket for the SendMetrics.ps1 script',
            'default': 'Onica-Monitor-Tools-Default'
        },        
    }

    def create_template(self):
        """Create the template."""
        template = self.template
        variables = self.get_variables()
        template.add_version('2010-09-09')
        template.add_description(TEMPLATE_DESCRIPTION)
        document_name =variables['DocumentName'].value
        try:
            if variables['DocumentContent'] == Ref('AWS::NoValue'):
                content = self.context.hook_data['json'][
                    variables['DocumentName'].value
                ]
            else:
                content = variables['DocumentContent']

        except KeyError:
            content = {'': ''}

        template.add_resource(ssm.Document(
            'SsmDocument',
            Content=content,
            DocumentType='Command'
        ))
        template.add_output(Output(
            'DocumentName',
            Description='Document to download and setup SencMetrics.ps1 on Windows server',
            Export=Export(Sub('${AWS::StackName}-SsmDocument')),  # nopep8 pylint: disable=C0301
            Value=Ref('SsmDocument')
        ))


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    print(BlueprintClass('test', Context({'namespace': 'test'})).to_json({
        'DocumentName': 'dummy-value'
    }))
