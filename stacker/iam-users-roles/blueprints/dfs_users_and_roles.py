"""Creates DFS IAM users, roles, and policies for DFS and Onica use."""
from __future__ import print_function
from os.path import dirname, realpath
import sys
import re
from troposphere import (
    And, Equals, Export, GetAtt, If, Output,
    iam, Not, Or, Ref, Sub, Condition, FindInMap
)

from awacs.aws import (
    Allow, Deny, Statement, Policy, Principal, Action
)

import awacs.aws

from awacs.aws import StringEquals

from awacs.aws import Condition as PolicyCondition

import awacs.cloudformation
import awacs.sts
import awacs.iam

from stacker.blueprints.base import Blueprint

from stacker.blueprints.variables.types import CFNString, CFNNumber


def version():
    """Call version function from top of repo."""
    root_dir = dirname(dirname(realpath(__file__)))
    if root_dir not in sys.path:
        sys.path.append(root_dir)
    import module_version  # pylint: disable=import-error
    return module_version.version()


TEMPLATE_DESCRIPTION = 'DFS Users, Groups, and Roles - {}'.format(
    version()
)
IAM_PREFIX = 'arn:${AWS::Partition}:iam::${AWS::AccountId}:'


class BlueprintClass(Blueprint):
    """Extends Stacker Blueprint class."""

    VARIABLES = {
        'CustomerName': {
            'type': CFNString,
            'description': 'Name of Customer.',
            'default': 'undefined'
        },
        'MasterAccountId': {
            'type': CFNString,
            'description': '(optional) Used when deploying for cross-account'
                           ' use to define the account that the user will be'
                           ' deployed to.',
            'default': 'undefined'
        },
        'SubAccounts': {
            'type': list,
            'description': '(optional) List of account IDs that pipeline '
                           'user can assume roles in. A list dicts with keys '
                           'id and role_name can also be provided if using a '
                           'custom role name.',
            'default': []
        },
        'MaxSessionDuration': {
            'type': CFNNumber,
            'description': 'Max duration for temporary credentials returned'
                           ' by AssumeRole. (seconds)',
            'default': 43200,
            'max_value': 43200,
            'min_value': 300
        },
        'Users': {
            'type': list,
            'description': 'List of dicts of name (email addresses) and group'
                           ' to be created.',
            'default': []
        },
        'DefaultRegion': {
            'type': CFNString,
            'description': '(optional) Provide an AWS region where user & '
                           'role will be deployed. Use when deployment runs '
                           'in multiple regions to restrict creation to one.',
            'default': 'undefined'
        }
    }

    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        self.template.add_version('2010-09-09')
        self.template.add_description(TEMPLATE_DESCRIPTION)
        variables = self.get_variables()

        default_region = template.add_condition(
            'DefaultRegionMatched',
            Or(
                Equals(variables['DefaultRegion'].ref, 'undefined'),
                Equals(variables['DefaultRegion'].ref, Ref('AWS::Region'))
            )
        )

        deploy_user = template.add_condition(
            'DeployPipelineUser',
            And(
                Condition(default_region),
                Or(
                    Equals(variables['MasterAccountId'].ref, 'undefined'),
                    Equals(
                        variables['MasterAccountId'].ref,
                        Ref('AWS::AccountId')
                    )
                )
            )
        )

        allow_assume_from_master = template.add_condition(
            'AllowCrossAccountAssume',
            And(
                Not(Equals(variables['MasterAccountId'].ref, 'undefined')),
                Not(Equals(
                    variables['MasterAccountId'].ref, Ref('AWS::AccountId')
                ))
            )
        )

        # some policy statements for the default group to all users to manage
        # themselves.
        default_policy = [Statement(
            Sid='AllowUserManageSelf',
            Effect=Allow,
            Action=[
                Action('iam', 'Get*'),
                Action('iam', 'List*'),
                Action('iam', 'Create*'),
                Action('iam', 'Delete*'),
                awacs.iam.DeactivateMFADevice,
                awacs.iam.EnableMFADevice,
                awacs.iam.ResyncMFADevice,
                awacs.iam.UpdateSigningCertificate,
                awacs.iam.UploadSigningCertificate,
                awacs.iam.UpdateSSHPublicKey,
                awacs.iam.UploadSSHPublicKey,
                awacs.iam.ResetServiceSpecificCredential,
                awacs.iam.UpdateServiceSpecificCredential,
                awacs.iam.ChangePassword
            ],
            Resource=[
                'arn:aws:iam::*:mfa/${aws:username}',
                'arn:aws:iam::*:user/${aws:username}'
            ]
        ), Statement(
            Sid='AllowNonResourceBasedReadOnly',
            Effect=Allow,
            Action=[
                awacs.iam.GetAccountSummary,
                awacs.iam.GetAccountPasswordPolicy,
                awacs.iam.ListUsers,
                awacs.iam.ListVirtualMFADevices,
                awacs.iam.ListAccountAliases
            ],
            Resource=['*']
        )]

        # sets the max allowed permissions of a user
        user_boundary = template.add_resource(iam.ManagedPolicy(
            'UserPermissionBoundary',
            PolicyDocument=Policy(
                Version='2012-10-17',
                Statement=default_policy + [Statement(
                    Sid='AllowAssumeRole',
                    Effect=Allow,
                    Action=[awacs.sts.AssumeRole],
                    Resource=['*']
                )]
            )
        ))
        template.add_output(Output(
            'UserPermissionBoundary',
            Description='IAM Policy used as a boundary.',
            Export=Export(Sub('${AWS::StackName}-UserBoundary')),
            Value=Ref(user_boundary)
        ))

        default_group = template.add_resource(iam.Group(
            'DefaultGroup',
            Condition=deploy_user,
            GroupName=Sub(
                '${CustomerName}-DefaultGroup'
            ),
            # contains permissions that allow users to reset their own
            # password and MFA token. Also contains explicit deny
            # if missing MFA.
            Policies=[iam.Policy(
                PolicyName='default-group-policy',
                PolicyDocument=Policy(
                    Version='2012-10-17',
                    Statement=[Statement(
                        Sid='BlockMostAccessUnlessSignedInWithMFA',
                        Effect=Deny,
                        NotAction=[
                            awacs.iam.ListMFADevices,
                            awacs.iam.ListUsers,
                            awacs.iam.GetUser,
                            awacs.iam.GetLoginProfile,
                            awacs.iam.ListVirtualMFADevices,
                            awacs.iam.CreateVirtualMFADevice,
                            awacs.iam.EnableMFADevice,
                            awacs.iam.ListVirtualMFADevices,
                            awacs.iam.ResyncMFADevice,
                            awacs.iam.ChangePassword
                        ],
                        Resource=['*'],
                        Condition=PolicyCondition(StringEquals({
                            'aws:MultiFactorAuthPresent': "false"
                        }))
                    )] + default_policy
                )
            )]
        ))

        # allowes users to assume any role
        admin_group = template.add_resource(iam.Group(
            'AdminGroup',
            Condition=deploy_user,
            GroupName=Sub(
                '${CustomerName}-AdminGroup'
            ),
            Policies=[iam.Policy(
                PolicyName=Sub(
                    'assume-${CustomerName}-AdminGroup'
                ),
                PolicyDocument=Policy(
                    Version='2012-10-17',
                    Statement=[Statement(
                        Sid='AllowAssumeRole',
                        Effect=Allow,
                        Action=[awacs.sts.AssumeRole],
                        Resource=[Sub(
                            'arn:aws:iam::*:role/${CustomerName}-AdminRole'
                        )]
                    )]
                )
            )]
        ))

        # mapping of groups to allow support for additional user groups
        map_group_to_access_level = {
            'admin': admin_group
        }

        for user in variables['Users']:
            template.add_resource(iam.User(
                re.sub(r'[\W+_]', '', user['name']),
                Condition=deploy_user,
                UserName=user['name'],
                Groups=[
                    Ref(default_group),
                    Ref(map_group_to_access_level.get(
                        user.get('group', ''), 'AWS::NoValue'
                    ))
                ],
                PermissionsBoundary=Ref(user_boundary)
            ))

        # admin role that is closer to PowerUser+
        admin_role = template.add_resource(iam.Role(
            'AdminRole',
            Condition=default_region,
            RoleName=Sub(
                '${CustomerName}-AdminRole'
            ),
            AssumeRolePolicyDocument=Policy(
                Version='2012-10-17',
                Statement=[Statement(
                    Sid='AllowAssumeRole',
                    Effect=Allow,
                    Action=[awacs.sts.AssumeRole],
                    Principal=Principal(
                        'AWS', [
                            Ref('AWS::AccountId'),
                            If(
                                allow_assume_from_master,
                                variables['MasterAccountId'].ref,
                                Ref('AWS::NoValue')
                            )
                        ]
                    )
                )]),
            MaxSessionDuration=variables['MaxSessionDuration'].ref,
            ManagedPolicyArns=[
                'arn:aws:iam::aws:policy/AdministratorAccess'
            ],
            Policies=[iam.Policy(
                PolicyName=Sub('${CustomerName}-AdminRole-Deny'),
                PolicyDocument=Policy(
                    Version='2012-10-17',
                    Statement=[Statement(
                        Sid='DenyResourceBased',
                        Effect=Deny,
                        Action=[
                            Action('*')
                        ],
                        Resource=[
                            Sub(IAM_PREFIX + 'group/*'),
                            Sub(IAM_PREFIX + 'mfa/*'),
                            Sub(IAM_PREFIX + 'user/*'),
                            FindInMap(
                                'Accounts',
                                Ref('AWS::AccountId'),
                                'ssoRole'
                            ),
                            Sub(
                                IAM_PREFIX + 'role/${CustomerName}-AdminRole'
                            ),
                            Sub(
                                'arn:${AWS::Partition}:s3:::${CustomerName}'
                                '-core-*'
                            ),
                            Sub(
                                'arn:${AWS::Partition}:cloudformation:*:'
                                '${AWS::AccountId}:stack/onica-*'
                            ),
                            Sub(
                                'arn:${AWS::Partition}:cloudformation:*:'
                                '${AWS::AccountId}:stack/dfs-*'
                            ),
                            Ref(user_boundary)
                        ]
                    ), Statement(
                        Sid='DenyNonResourceBased',
                        Effect=Deny,
                        Action=[
                            Action('account', '*'),
                            Action('organizations', '*')
                        ],
                        Resource=['*']
                    )]
                )
            )]
        ))
        template.add_output(Output(
            'AdminRole',
            Description='Role assumed for admin deployments.',
            Export=Export(Sub('${AWS::StackName}-AdminRole')),
            Value=If(
                default_region,
                GetAtt(admin_role, 'Arn'),
                Sub(
                    'arn:${AWS::Partition}:iam::${AWS::AccountId}:'
                    'role/${CustomerName}-AdminRole'
                )
            )
        ))
        template.add_output(Output(
            'AssumeAdminRoleURL',
            Description='URL for Assume Admin Role.',
            Export=Export(Sub('${AWS::StackName}-AssumeAdminURL')),
            Value=Sub(
                'https://signin.aws.amazon.com/switchrole?roleName='
                '${CustomerName}-AdminRole&account=${AWS::AccountId}'
            )
        ))


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    print(BlueprintClass('test', Context({'namespace': 'test'})).to_json({
        'Users': [
            {
                'name': 'admin@example.com',
                'group': 'admin'
            }, {
                'name': 'dummy_user@example.com'
            }
        ]
    }))
