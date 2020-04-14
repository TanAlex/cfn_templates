#!/usr/bin/env python
"""Stacker module for creating a Squid ASG."""

from troposphere import (
    Base64, Join, Output, Ref, Sub, Export, ec2,
    And, Not, Equals, iam, autoscaling, If, Select, Split
)
from modules.squid_server.module_version import version
import awacs.ec2
import awacs.s3
import awacs.ssm
import awacs.sts
from awacs.aws import Allow, Policy, Principal, Statement
# Linter is incorrectly flagging the automatically generated functions in awacs
from awacs.aws import StringEquals, StringLike  # noqa pylint: disable=no-name-in-module

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import (
    CFNCommaDelimitedList, CFNNumber, CFNString,
    EC2SubnetIdList
)

TEMPLATE_DESCRIPTION = 'Squid Cluster - {}'.format(version())


class AutoScalingGroup(Blueprint):
    """Extend Stacker Blueprint class."""

    VARIABLES = {
        'AppAMI': {
            'type': CFNString,  # Not EC2ImageId to allow blank value
            'description': 'AMI ID for app instances; leave blank to '
                           'automatically look up the via "AMILookupArn".',
            'default': ''
        },
        'AppInstanceType': {
            'type': CFNString,
            'description': 'Type of the management instances',
            'default': 'm3.medium'
        },
        'AppPolicies': {
            'type': CFNCommaDelimitedList,
            'description': 'IAM managed policy ARNs to apply to the instances'
        },
        'AppSubnets': {
            'type': EC2SubnetIdList,
            'description': 'Subnets in which the app server(s) will be'
                           ' deployed'
        },
        'AppSecurityGroups': {
            'type': CFNCommaDelimitedList,
            'description': 'Security groups to apply to the instances',
            'default': ''
        },
        'ApplicationName': {
            'type': CFNString,
            'description': 'Instance name tag value (will have "CustomerName" '
                           'prepended and "EnvironmentName" appended to it)',
            'default': 'application'
        },
        'ASGMinValue': {
            'type': CFNString,
            'description': 'Minimum number of instances that will be running '
                           'in the autoscaling group',
            'default': '1'
        },
        'ASGDesiredValue': {
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
        'AppVolumeName': {
            'type': CFNString,
            'description': 'Instance EBS volume name',
            'default': '/dev/xvda'
        },
        'AppVolumeSize': {
            'type': CFNNumber,
            'description': 'Size of instance EBS volume in GB',
            'default': '15'
        },
        'AppVolumeType': {
            'type': CFNString,
            'description': 'Instance EBS volume type',
            'allowed_values': [
                'standard',
                'io1',
                'gp2'
            ],
            'default': 'gp2'
        },
        'CustomerName': {
            'type': CFNString,
            'description': 'The nickname for the customer/tenant. Must be all'
                           ' lowercase letters, should not contain spaces or '
                           'special characters, nor should it include any part'
                           ' of EnvironmentName',
            'allowed_pattern': '[-_ a-z]*',
            'default': 'edwards'
        },
        'CWAgentMetricsCollection': {
            'type': CFNString,
            'description': 'Should the CloudWatch Agent metrics be published?',
            'default': 'false',
            'allowed_values': [
                'true',
                'false'
            ]
        },
        'CWAgentConfig': {
            'type': CFNString,
            'description': 'CW Agent config JSON',
            'default': 'standard_conf.json',
        },
        'ELBNames': {
            'type': CFNCommaDelimitedList,
            'description': '(Optional) ELBs to associate with the app ASG.',
            'default': ''
        },
        'EnvironmentName': {
            'type': CFNString,
            'description': 'Name of Environment',
            'default': 'common'
        },
        'HealthCheckGracePeriod': {
            'type': CFNNumber,
            'description': 'ASG health check grace period (in seconds)',
            'default': '600'
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
        # Not using EC2KeyPairKeyName to allow KeyName to be optional
        'KeyName': {
            'type': CFNString,
            'description': 'Name of an existing EC2-VPC KeyPair',
            'default': ''
        },
        'MetricsCollection': {
            'type': CFNString,
            'description': 'Should the autoscaling have metrics?',
            'default': 'true',
            'allowed_values': [
                'true',
                'false'
            ]
        },
        'MetricsCollectionGranularity': {
            'type': CFNString,
            'description': 'How often to pull metrics',
            'default': '1Minute'
        },
        'TargetGroupARNs': {
            'type': CFNCommaDelimitedList,
            'description': '(Optional) Target groups to associate with the '
                           'app ASG.',
            'default': ''
        },
        "UserData": {
            "type": CFNString,
            "description": "Instance user data",
            "default": ''
        },
        'CostCenter': {
            'type': CFNString,
            'description': 'Tag value.',
            'default': '0'
        },
        'TechOwner': {
            'type': CFNString,
            'description': 'Tag value.',
            'default': 'Onica'
        },
        'TechOwnerEmail': {
            'type': CFNString,
            'description': 'Tag value.',
            'default': 'incidents@onica.com'
        },
        'DataClassification': {
            'type': CFNString,
            'description': 'Data Classification level',
            'default': 'none',
            'allowed_values': [
                'none',
                'sensitive',
                'regulated',
                'sensitive_regulated'
            ]
        },
        'VpcId': {
            'type': CFNString,
            'description': 'What VPC is this being deployed to?'
        },
        'NLBIps': {
            'type': str,
            'description': 'comma separated ips',
            'default': '0.0.0.0'
        },
        'InternalNLBIps': {
            'type': str,
            'description': 'comma separated internal ips',
            'default': '192.168.0.1'
        },
        'BastionSG': {
            'type': CFNString,
            'description': 'sg to allow bastion connection'
        }
    }

    def add_asg(self):
        """Add ASG to template."""
        template = self.template
        variables = self.get_variables()
        external_ip_list = variables['NLBIps'].split(',')
        internal_ip_list = variables['InternalNLBIps'].split(',')
        ip_list = []
        ip_list.extend(external_ip_list)
        ip_list.extend(internal_ip_list)
        # Conditions
        sshkeyspecified = 'SSHKeySpecified'
        template.add_condition(
            sshkeyspecified,
            And(
                Not(Equals(variables['KeyName'].ref, '')),
                Not(Equals(variables['KeyName'].ref, 'undefined'))
            )
        )

        additional_sgs = 'AdditionalSGs'
        template.add_condition(
            additional_sgs,
            Not(Equals(variables['AppSecurityGroups'].value, ''))
        )

        metricscollectionomitted = 'MetricsCollectionOmitted'
        template.add_condition(
            metricscollectionomitted,
            Equals(variables['MetricsCollection'].ref, 'false')
        )

        elbnamesomitted = 'ELBNamesOmitted'
        template.add_condition(
            elbnamesomitted,
            Equals(Select(0, variables['ELBNames'].ref), '')
        )

        targetgrouparnsomitted = 'TargetGroupARNsOmitted'
        template.add_condition(
            targetgrouparnsomitted,
            Equals(Join('', variables['TargetGroupARNs'].ref), '')
        )
        instance_sg = template.add_resource(
            ec2.SecurityGroup(
                'InstanceSG',
                GroupName='InstanceSG',
                GroupDescription='The security group for squid EC2 instances',
                VpcId=variables['VpcId'].ref
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'InstanceSGIngressSSH',
                GroupId=Ref(instance_sg),
                FromPort=22,
                ToPort=22,
                Description='SSH port',
                SourceSecurityGroupId=variables['BastionSG'].ref,
                IpProtocol='tcp'
            )
        )

        for ip in ip_list:
            template.add_resource(
                ec2.SecurityGroupIngress(
                    'InstanceSGAccessFromNLB{}'.format(ip.replace('.', '')),
                    GroupId=Ref(instance_sg),
                    FromPort=3128,
                    ToPort=3128,
                    Description='Access from NLBs',
                    CidrIp=ip+'/32',
                    IpProtocol='tcp'
                )
            )
        template.add_output(Output(
            "{}ARN".format(instance_sg.title),
            Description='Instance SG',
            Value=Ref(instance_sg)
        ))

        squidproxyrole = template.add_resource(
            iam.Role(
                'SquidProxyRole',
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
                Path='/'
            )
        )

        ec2instanceprofile = template.add_resource(
            iam.InstanceProfile(
                'EC2InstanceProfile',
                Path='/',
                Roles=[Ref(squidproxyrole)]
            )
        )
        proxy_instances = template.add_resource(
            autoscaling.LaunchConfiguration(
                'ProxyInstances',
                AssociatePublicIpAddress=True,
                BlockDeviceMappings=[
                    ec2.BlockDeviceMapping(
                        DeviceName=variables['AppVolumeName'].ref,
                        Ebs=ec2.EBSBlockDevice(
                            DeleteOnTermination=True,
                            VolumeSize=variables['AppVolumeSize'].ref,
                            VolumeType=variables['AppVolumeType'].ref
                        )
                    )
                ],
                IamInstanceProfile=Ref(ec2instanceprofile),
                ImageId=variables['AppAMI'].ref,
                InstanceType=variables['AppInstanceType'].ref,
                InstanceMonitoring=True,
                KeyName=If(
                    sshkeyspecified,
                    variables['KeyName'].ref,
                    Ref('AWS::NoValue')
                ),
                SecurityGroups=Split(',', Join(',', [Ref(instance_sg), If(
                    additional_sgs,
                    variables['AppSecurityGroups'].value,
                    Ref('AWS::NoValue'))])),
                UserData=Base64(Join('', [variables['UserData'].ref]))
            )
        )

        clusterasg = template.add_resource(
            autoscaling.AutoScalingGroup(
                'AutoScalingGroup',
                MinSize=variables['ASGMinValue'].ref,
                DesiredCapacity=variables['ASGDesiredValue'].ref,
                MaxSize=variables['ASGMaxValue'].ref,
                HealthCheckGracePeriod=variables['HealthCheckGracePeriod'].ref,
                HealthCheckType=variables['HealthCheckType'].ref,
                MetricsCollection=If(
                    metricscollectionomitted,
                    Ref('AWS::NoValue'),
                    [autoscaling.MetricsCollection(
                        Granularity=variables['MetricsCollectionGranularity']
                        .ref
                    )]
                ),
                LaunchConfigurationName=Ref(proxy_instances),
                LoadBalancerNames=If(
                    elbnamesomitted,
                    Ref('AWS::NoValue'),
                    variables['ELBNames'].ref
                ),
                Tags=autoscaling.Tags(
                    Name=Join('-', [variables['CustomerName'].ref,
                                    variables['ApplicationName'].ref,
                                    variables['EnvironmentName'].ref]),
                    Company=variables['CustomerName'].ref,
                    Application=variables['ApplicationName'].ref,
                    Environment=variables['EnvironmentName'].ref,
                    CostCenter=variables['CostCenter'].ref,
                    TechOwner=variables['TechOwner'].ref,
                    TechOwnerEmail=variables['TechOwnerEmail'].ref,
                    DataClassification=variables['DataClassification'].ref,

                ),
                TargetGroupARNs=If(
                    targetgrouparnsomitted,
                    Ref('AWS::NoValue'),
                    variables['TargetGroupARNs'].ref
                ),
                VPCZoneIdentifier=variables['AppSubnets'].ref
            )
        )

        template.add_output(Output(
            clusterasg.title,
            Description='Name of autoscaling group',
            Export=Export(Sub('${AWS::StackName}-%s' % clusterasg.title)),
            Value=Ref(clusterasg),
        ))

    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        template.set_version('2010-09-09')
        template.set_description(TEMPLATE_DESCRIPTION)
        self.add_asg()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context
    print(AutoScalingGroup('test',
                           Context({"namespace": "test"})).to_json())
