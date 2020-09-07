#!/usr/bin/env python
"""Stacker module for creating a lambda function for looking up AMIs."""
from __future__ import print_function
from os import path
from os.path import dirname, realpath
import sys

from troposphere import (
    AWSHelperFn, Export, GetAtt, Join, Output, Ref, Sub, awslambda, iam
)

import awacs.awslambda
import awacs.ec2
from awacs.aws import Allow, PolicyDocument, Statement
from awacs.helpers.trust import make_simple_assume_policy

from stacker.lookups.handlers.file import parameterized_codec
from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString

AWS_LAMBDA_DIR = path.join(path.dirname(path.realpath(__file__)),
                           'aws_lambda')
IAM_ARN_PREFIX = 'arn:aws:iam::aws:policy/service-role/'


class AmiLookup(Blueprint):
    """Extends Stacker Blueprint class."""

    ami_lookup_src = parameterized_codec(
        open(path.join(AWS_LAMBDA_DIR, 'ami_lookup', 'index.py'), 'r').read(),
        False  # disable base64 encoding
    )

    VARIABLES = {
        'AMILookupLambdaFunction': {'type': AWSHelperFn,
                                    'description': 'Lambda function code',
                                    'default': ami_lookup_src},
        'CustomerName': {'type': CFNString,
                         'description': 'The nickname for the new customer. '
                                        'Must be all lowercase letters, '
                                        'should not contain spaces or special '
                                        'characters, nor should it include '
                                        'any part of EnvironmentName.',
                         'allowed_pattern': '[-_ a-z]*',
                         'default': ''},
        'EnvironmentName': {'type': CFNString,
                            'description': 'Name of Environment',
                            'default': 'common'}
    }

    def add_resources_and_outputs(self):
        """Add resources and outputs to template."""
        template = self.template
        variables = self.get_variables()

        amilookuplambdarole = template.add_resource(
            iam.Role(
                'AMILookupLambdaRole',
                AssumeRolePolicyDocument=make_simple_assume_policy(
                    'lambda.amazonaws.com'
                ),
                ManagedPolicyArns=[
                    IAM_ARN_PREFIX + 'AWSLambdaBasicExecutionRole'
                ],
                Policies=[
                    iam.Policy(
                        PolicyName=Join('-', ['amilookup-lambda-role',
                                              variables['EnvironmentName'].ref,
                                              variables['CustomerName'].ref]),
                        PolicyDocument=PolicyDocument(
                            Version='2012-10-17',
                            Statement=[
                                Statement(
                                    Action=[awacs.ec2.DescribeImages],
                                    Effect=Allow,
                                    Resource=['*'],
                                    Sid='AMIAccess'
                                )
                            ]
                        )
                    )
                ]
            )
        )

        # If uploaded to S3 via stacker hook, use that URL; otherwise fall back
        # to the inline code
        if ('lambda' in self.context.hook_data and
                'CoreAMILookup' in self.context.hook_data['lambda']):
            code = self.context.hook_data['lambda']['CoreAMILookup']
        else:
            code = awslambda.Code(
                ZipFile=variables['AMILookupLambdaFunction']
            )

        amilookup = template.add_resource(
            awslambda.Function(
                'AMILookup',
                Description='Find latest AMI for given platform',
                Code=code,
                Handler='index.handler',
                Role=GetAtt(amilookuplambdarole, 'Arn'),
                Runtime='python2.7',
                Timeout=60
            )
        )
        template.add_output(
            Output(
                'FunctionName',
                Description='AMI lookup function name',
                Export=Export(
                    Sub('${AWS::StackName}-FunctionName')
                ),
                Value=Ref(amilookup)
            )
        )
        template.add_output(
            Output(
                'FunctionArn',
                Description='AMI lookup function Arn',
                Export=Export(
                    Sub('${AWS::StackName}-FunctionArn')
                ),
                Value=GetAtt(amilookup, 'Arn')
            )
        )
        template.add_output(
            Output(
                'FunctionRegion',
                Description='AMI lookup function region',
                Value=Ref('AWS::Region')
            )
        )

        # IAM Instance Roles and Profiles
        amilookupaccesspolicy = template.add_resource(
            iam.ManagedPolicy(
                'AmiLookupAccessPolicy',
                Description='Allows invocation of the AMI lookup lambda '
                            'function.',
                Path='/',
                PolicyDocument=PolicyDocument(
                    Version='2012-10-17',
                    Statement=[
                        Statement(
                            Action=[awacs.awslambda.InvokeFunction],
                            Effect=Allow,
                            Resource=[GetAtt(amilookup, 'Arn')]
                        )
                    ]
                )
            )
        )
        template.add_output(
            Output(
                'AccessPolicy',
                Description='Policy allowing use of the AMI lookup lambda '
                            'function',
                Export=Export(
                    Sub('${AWS::StackName}-%s' % 'AccessPolicy')
                ),
                Value=Ref(amilookupaccesspolicy)
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.add_version('2010-09-09')
        self.template.add_description("Sturdy Platform - Core - AMI Lookup "
                                      "- {0}".format(version()))
        self.add_resources_and_outputs()


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

    print(AmiLookup('test',
                    Context({'namespace': 'test'}),
                    None).to_json())
