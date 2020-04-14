"""Creates ASCTrac App ASG."""
from os import path
from os.path import dirname, realpath
import sys

from troposphere import (
    Sub, Tags, Output, Ref, ssm,
    ec2, iam, Join, autoscaling, AWSHelperFn
)

import awacs.ec2
import awacs.s3
import awacs.ssm
import awacs.sts
from awacs.aws import Allow, Policy, Principal, Statement, Condition
# generated at runtime so has to be imported separately
from awacs.aws import StringEquals  # pylint: disable=no-name-in-module

from stacker.lookups.handlers.file import parameterized_codec
from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import (
    CFNCommaDelimitedList, CFNNumber, CFNString, EC2SubnetIdList
)

BLUEPRINT_FOLDER = dirname(realpath(__file__))
USERDATA_DIR = path.join(
    BLUEPRINT_FOLDER, 'scripts/')


def version():
    """Call version function from top of repo."""
    root_dir = dirname(dirname(realpath(__file__)))
    if root_dir not in sys.path:
        sys.path.append(root_dir)
    import module_version  # pylint: disable=import-error
    return module_version.version()


TEMPLATE_DESCRIPTION = 'ASCTrac App ASG - {}'.format(version())

AWS_POLICY_PREFIX = 'arn:aws:iam::aws:policy/'


class BlueprintClass(Blueprint):
    """Extend Stacker Blueprint class."""

    userdata_src = parameterized_codec(
        open(path.join(USERDATA_DIR, 'asctrac_userdata.ps'), 'r').read(),
        True  # enable base64 encoding
    )

    VARIABLES = {
        'AppAMI': {
            'type': CFNString,
            'description': 'AMI ID for app instances',
            'default': 'ami-0a6b96ce710e139e3'  # MS Server 2016 Base
        },
        'UserData': {'type': AWSHelperFn,
                     'description': 'Instance user data',
                     'default': userdata_src},
        'AppInstanceType': {
            'type': CFNString,
            'description': 'Type of the instances',
            'default': 'm5.xlarge'
        },
        'AppPolicies': {
            'type': CFNCommaDelimitedList,
            'description': 'IAM managed policy ARNs to apply to the instances',
            'default': 'arn:aws:iam::aws:policy/service-role/'
                       'AmazonEC2RoleforSSM,arn:aws:iam::aws:policy/'
                       'CloudWatchAgentServerPolicy'
        },
        'AppSubnets': {
            'type': EC2SubnetIdList,
            'description': 'Subnets in which the app server(s) will be'
                           ' deployed'
        },
        'OnPremCIDR': {
            'type': CFNString,
            'description': 'On Premise CIDR Block'
        },
        'VpcId': {
            'type': CFNString,
            'description': 'VPC ID of ASCTrac Security Group'
        },
        'ASGMinValue': {
            'type': CFNString,
            'description': 'Minimum number of instances that will be running '
                           'in the autoscaling group',
            'default': '1'
        },
        'ASGMaxValue': {
            'type': CFNString,
            'description': 'Maximum number of instances that will be running '
                           'in the autoscaling group',
            'default': '1'
        },
        'HealthCheckGracePeriod': {
            'type': CFNNumber,
            'description': 'ASG health check grace period (in seconds)',
            'default': '300'
        },
        'HealthCheckType': {
            'type': CFNString,
            'description': 'Type of ASG health check',
            'default': 'EC2',
            'allowed_values': [
                'EC2',
                'ELB'
            ]
        },
        'KeyName': {
            'type': CFNString,
            'description': 'Name of an existing EC2-VPC KeyPair',
            'default': ''
        },
        'ApplicationName': {
            'type': CFNString,
            'description': 'Instance name tag value (will have "Customer" '
                           'prepended and "Environment" appended to it)'
        },
        'CustomerName': {
            'type': CFNString,
            'description': 'Name of Customer'
        },
        'ApplicationTier': {
            'type': CFNString,
            'description': 'Tier of Application',
            'default': 'application'
        },
        'EnvironmentName': {
            'type': CFNString,
            'description': 'Name of Environment'
        },
        'CostCenter': {
            'type': CFNString,
            'description': 'Cost Center Number',
        },
        'TechOwner': {
            'type': CFNString,
            'description': 'Name of Tech Owner',
            'default': 'platform'
        },
        'TechOwnerEmail': {
            'type': CFNString,
            'description': 'Name of Tech Owner Email',
            'default': ''
        },
        'Backup': {
            'type': CFNString,
            'description': 'Tag value. Used to enable snapshots and/or '
                           'join a backup group.',
            'default': 'True'
        },
        'DataClassification': {
            'type': CFNString,
            'description': 'Tag value.',
            'default': 'none',
            'allowed_values': [
                'none', 'sensitive', 'regulated', 'sensitive-regulated'
            ]
        },
        'Associations': {
            'type': list,
            'description': 'List of SSM Documents for SSM Association',
            'default': ['dfs-prod-cloudwatch-agent-SsmDocument-1ACK8RNMCRHLR']
        },
        'SSMParameter': {
            'type': CFNString,
            'description': 'Name of SSM Paramter used in SSM Association',
            'default': 'AmazonCloudWatch-windows-config'
        },
        'SSMDocument': {
            'type': CFNString,
            'description': 'Name of SSM Document used in SSM Association',
            'default': 'dfs-prod-cloudwatch-agent-SsmDocument-1ACK8RNMCRHLR'
        }
    }

    def add_resources(self):
        """Adds resources to template."""
        # pylint: disable=too-many-locals
        template = self.template
        variables = self.get_variables()

        common_tags = {
            'Environment': variables['EnvironmentName'].ref,
            'Application': variables['ApplicationName'].ref,
            'ApplicationTier': variables['ApplicationTier'].ref,
            'CostCenter': variables['CostCenter'].ref,
            'TechOwner': variables['TechOwner'].ref,
            'TechOwnerEmail': variables['TechOwnerEmail'].ref,
            'Backup': variables['Backup'].ref,
            'DataClassification': variables['DataClassification'].ref
        }

        # Security Groups
        asctrac_sg = template.add_resource(ec2.SecurityGroup(
            'ASCTracSG',
            GroupName='asctrac-sg',
            GroupDescription='SG for ASCTrac Instance',
            VpcId=variables['VpcId'].ref,
            Tags=Tags(
                Name=Sub(
                    '${CustomerName}-${ApplicationName}-sg-'
                    '${EnvironmentName}'
                ), **common_tags
            )

        ))

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort80',
                GroupId=Ref(asctrac_sg),
                FromPort=80,
                ToPort=80,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort135',
                GroupId=Ref(asctrac_sg),
                FromPort=135,
                ToPort=135,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort445',
                GroupId=Ref(asctrac_sg),
                FromPort=445,
                ToPort=445,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort700',
                GroupId=Ref(asctrac_sg),
                FromPort=700,
                ToPort=700,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort1433',
                GroupId=Ref(asctrac_sg),
                FromPort=1433,
                ToPort=1433,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort3389',
                GroupId=Ref(asctrac_sg),
                FromPort=3389,
                ToPort=3389,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort5985',
                GroupId=Ref(asctrac_sg),
                FromPort=5985,
                ToPort=5985,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort47001',
                GroupId=Ref(asctrac_sg),
                FromPort=47001,
                ToPort=47001,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort49152',
                GroupId=Ref(asctrac_sg),
                FromPort=49152,
                ToPort=49152,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort49153',
                GroupId=Ref(asctrac_sg),
                FromPort=49153,
                ToPort=49153,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort49154',
                GroupId=Ref(asctrac_sg),
                FromPort=49154,
                ToPort=49154,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort49185',
                GroupId=Ref(asctrac_sg),
                FromPort=49185,
                ToPort=49185,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort49214',
                GroupId=Ref(asctrac_sg),
                FromPort=49214,
                ToPort=49214,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort49251',
                GroupId=Ref(asctrac_sg),
                FromPort=49251,
                ToPort=49251,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'ASCTracPort1434',
                GroupId=Ref(asctrac_sg),
                FromPort=1434,
                ToPort=1434,
                Description='',
                CidrIp=variables['OnPremCIDR'].ref,
                IpProtocol='tcp'
            )
        )

        template.add_output(Output(
            'ASCTracSG',
            Description='ASCTrac Security Group ID',
            Value=Ref(asctrac_sg)
        ))

    # IAM
        asctrac_role = template.add_resource(
            iam.Role(
                'ASCTracRole',
                AssumeRolePolicyDocument=Policy(
                    Version='2012-10-17',
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[awacs.sts.AssumeRole],
                            Principal=Principal('Service',
                                                ['ec2.amazonaws.com'])
                        )
                    ]
                ),
                ManagedPolicyArns=variables['AppPolicies'].ref,
                Path='/',
                Policies=[iam.Policy(
                    PolicyName='AllowASCTracSSM',
                    PolicyDocument=Policy(
                        Version='2012-10-17',
                        Statement=[Statement(
                            Sid='ASCTracSSMParameters',
                            Effect=Allow,
                            Action=[
                                awacs.ssm.GetParameters,
                                awacs.ssm.GetParameter
                            ],
                            Resource=[Sub(
                                'arn:${AWS::Partition}:ssm:${AWS::Region}:'
                                '${AWS::AccountId}:parameter/asctrac/*'
                            )]
                        ),
                            Statement(
                                Sid='ASCTracS3Permissions',
                                Effect=Allow,
                                Action=[
                                    awacs.s3.GetObject,
                                    awacs.s3.ListObjects
                                ],
                                Resource=[Sub(
                                    'arn:${AWS::Partition}:s3:::'
                                    'dfs-${AWS::Region}-asctrac/*'
                                )]
                        ),
                            Statement(
                                Sid='ASCTracEC2Permissions',
                                Effect=Allow,
                                Action=[
                                    awacs.ec2.DescribeInstances,
                                    awacs.ec2.DescribeTags,
                                    awacs.ec2.CreateTags
                                ],
                                Resource=[Sub(
                                    'arn:${AWS::Partition}:ec2:${AWS::Region}:'
                                    '${AWS::AccountId}:instance/*'
                                )],
                                Condition=Condition(StringEquals({
                                    'ec2:ResourceTag/'
                                    'aws:cloudformation:stack-name':
                                        Ref('AWS::StackName')
                                }))
                        )]
                    )
                )]
            )
        )

    # Instance Resources
        asctrac_instance_profile = template.add_resource(
            iam.InstanceProfile(
                'EC2InstanceProfile',
                Path='/',
                Roles=[Ref(asctrac_role)]
            )
        )

    # Autoscaling Group
        server_launch_config = template.add_resource(
            autoscaling.LaunchConfiguration(
                'LaunchConfig',
                IamInstanceProfile=Ref(asctrac_instance_profile),
                ImageId=variables['AppAMI'].ref,
                InstanceType=variables['AppInstanceType'].ref,
                InstanceMonitoring=True,
                KeyName=variables['KeyName'].ref
                if variables['KeyName'].value else Ref(
                    'AWS::NoValue'),
                SecurityGroups=[Ref(asctrac_sg)],
                UserData=variables['UserData'],
                BlockDeviceMappings=[
                    ec2.BlockDeviceMapping(
                        DeviceName='/dev/sda1',
                        Ebs=ec2.EBSBlockDevice(
                            Encrypted='true',
                            DeleteOnTermination=True,
                            VolumeSize='400',
                            VolumeType='gp2'
                        )
                    )
                ]
            )
        )

        server_asg = template.add_resource(
            autoscaling.AutoScalingGroup(
                'AutoScaleGroup',
                MinSize=variables['ASGMinValue'].ref,
                MaxSize=variables['ASGMaxValue'].ref,
                HealthCheckGracePeriod=variables['HealthCheckGracePeriod'].ref,
                HealthCheckType=variables['HealthCheckType'].ref,
                MetricsCollection=[autoscaling.MetricsCollection(
                    Granularity='1Minute'
                )],
                LaunchConfigurationName=Ref(server_launch_config),
                VPCZoneIdentifier=variables['AppSubnets'].ref,
                Tags=[autoscaling.Tag('Name', Join('-', [
                    'dfs',
                    variables['EnvironmentName'].ref,
                    variables['ApplicationName'].ref,
                    'asg'
                ]), True)] + [autoscaling.Tag(
                    key, value, True
                ) for key, value in common_tags.items()]
            )
        )

        template.add_output(Output(
            'ASG',
            Description='Name of autoscaling group',
            Value=Ref(server_asg),
        ))

        # SSM Association
        template.add_resource(ssm.Association(
            'ASCTracCWAgentAssociation',
            DependsOn=server_asg.title,
            Name=variables['SSMDocument'].ref,
            AssociationName='ASCTracConfigureCWAgent',
            Targets=[ssm.Targets(
                Key='tag:Name',
                Values=[Join('-', [
                    'dfs',
                    variables['EnvironmentName'].ref,
                    variables['ApplicationName'].ref,
                    'asg'
                ])]
            )],
            Parameters={
                "configurationLocation": [variables['SSMParameter'].ref]
            }
        ))

    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        template.add_version('2010-09-09')
        template.add_description(TEMPLATE_DESCRIPTION)
        self.add_resources()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    print(BlueprintClass(
        'test',
        Context({'namespace': 'test'})).to_json())
