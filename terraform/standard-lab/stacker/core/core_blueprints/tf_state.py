#!/usr/bin/env python
"""Module with Terraform state resources."""
from __future__ import print_function
from os.path import dirname, realpath
import sys

from troposphere import (
    Equals, Export, GetAtt, If, Join, Or, Output, Ref, Sub, dynamodb, iam, s3
)

import awacs.dynamodb
import awacs.s3
from awacs.aws import Allow, PolicyDocument, Statement

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString


class TfState(Blueprint):
    """Stacker blueprint for creating Terraform state resources."""

    VARIABLES = {
        'BucketName': {'type': CFNString,
                       'description': '(optional) Name for the S3 bucket',
                       'default': ''},
        'TableName': {'type': CFNString,
                      'description': '(optional) Name for the DynamoDB table',
                      'default': ''}
    }

    def add_resources(self):
        """Add resources to template."""
        template = self.template
        variables = self.get_variables()

        for i in ['BucketName', 'TableName']:
            template.add_condition(
                "%sOmitted" % i,
                Or(Equals(variables[i].ref, ''),
                   Equals(variables[i].ref, 'undefined'))
            )

        terraformlocktable = template.add_resource(
            dynamodb.Table(
                # Not just locks now but can't change this resource name
                'TerraformLockTable',
                AttributeDefinitions=[
                    dynamodb.AttributeDefinition(
                        AttributeName='LockID',
                        AttributeType='S'
                    )
                ],
                KeySchema=[
                    dynamodb.KeySchema(
                        AttributeName='LockID',
                        KeyType='HASH'
                    )
                ],
                ProvisionedThroughput=dynamodb.ProvisionedThroughput(
                    ReadCapacityUnits=2,
                    WriteCapacityUnits=2
                ),
                TableName=If(
                    'TableNameOmitted',
                    Ref('AWS::NoValue'),
                    variables['TableName'].ref
                )
            )
        )
        template.add_output(Output(
            '%sName' % terraformlocktable.title,
            Description='Name of DynamoDB table for Terraform locks',
            Export=Export(Sub('${AWS::StackName}-'
                              '%sName' % terraformlocktable.title)),
            Value=Ref(terraformlocktable)
        ))

        terraformstatebucket = template.add_resource(
            s3.Bucket(
                'TerraformStateBucket',
                AccessControl=s3.Private,
                BucketName=If(
                    'BucketNameOmitted',
                    Ref('AWS::NoValue'),
                    variables['BucketName'].ref
                ),
                LifecycleConfiguration=s3.LifecycleConfiguration(
                    Rules=[
                        s3.LifecycleRule(
                            NoncurrentVersionExpirationInDays=90,
                            Status='Enabled'
                        )
                    ]
                ),
                VersioningConfiguration=s3.VersioningConfiguration(
                    Status='Enabled'
                )
            )
        )
        template.add_output(Output(
            '%sName' % terraformstatebucket.title,
            Description='Name of bucket storing Terraform state',
            Export=Export(Sub('${AWS::StackName}-'
                              '%sName' % terraformstatebucket.title)),
            Value=Ref(terraformstatebucket)
        ))
        template.add_output(Output(
            '%sArn' % terraformstatebucket.title,
            Description='Arn of bucket storing Terraform state',
            Export=Export(Sub('${AWS::StackName}-'
                              '%sArn' % terraformstatebucket.title)),
            Value=GetAtt(terraformstatebucket, 'Arn')
        ))

        managementpolicy = template.add_resource(
            iam.ManagedPolicy(
                'ManagementPolicy',
                Description='Managed policy for Terraform state management.',
                Path='/',
                PolicyDocument=PolicyDocument(
                    Version='2012-10-17',
                    Statement=[
                        # https://www.terraform.io/docs/backends/types/s3.html#s3-bucket-permissions
                        Statement(
                            Action=[awacs.s3.ListBucket],
                            Effect=Allow,
                            Resource=[GetAtt(terraformstatebucket, 'Arn')]
                        ),
                        Statement(
                            Action=[awacs.s3.GetObject,
                                    awacs.s3.PutObject],
                            Effect=Allow,
                            Resource=[
                                Join('', [GetAtt(terraformstatebucket, 'Arn'),
                                          '/*'])
                            ]
                        ),
                        Statement(
                            Action=[awacs.dynamodb.GetItem,
                                    awacs.dynamodb.PutItem,
                                    awacs.dynamodb.DeleteItem],
                            Effect=Allow,
                            Resource=[GetAtt(terraformlocktable, 'Arn')]
                        )
                    ]
                )
            )
        )
        template.add_output(
            Output(
                'PolicyArn',
                Description='Managed policy Arn',
                Export=Export(Sub('${AWS::StackName}-PolicyArn')),
                Value=Ref(managementpolicy)
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.add_version('2010-09-09')
        self.template.add_description("Sturdy Platform - Core - Terraform "
                                      " State - "
                                      "{0}".format(version()))
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

    print(TfState('test',
                  Context({'namespace': 'test'}),
                  None).to_json())
