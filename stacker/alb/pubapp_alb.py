"""Creates an ALB and SGs."""
from os.path import dirname, realpath
import sys

from troposphere import (
    And, Equals, Export, GetAtt, If, Sub, Tags, Not, Or, Output, Ref,
    ec2
)
from troposphere import elasticloadbalancingv2 as elbv2

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import (
    CFNString, CFNCommaDelimitedList
)


def version():
    """Call version function from top of repo."""
    root_dir = dirname(dirname(realpath(__file__)))
    if root_dir not in sys.path:
        sys.path.append(root_dir)
    import module_version  # pylint: disable=import-error
    return module_version.version()


TEMPLATE_DESCRIPTION = 'PUBAPP ALB - {}'.format(version())


class BlueprintClass(Blueprint):
    """Extend Stacker Blueprint class."""

    VARIABLES = {
        'CustomerName': {
            'type': CFNString,
            'description': 'The nickname for the customer/tenant. Must be all'
                           ' lowercase letters, should not contain spaces or '
                           'special characters, nor should it include any part'
                           ' of EnvironmentName',
            'allowed_pattern': '[-_ a-z]*',
            'default': 'courtcall'
        },
        'ApplicationName': {
            'type': CFNString,
            'description': 'Instance name tag value (will have "CustomerName" '
                           'prepended and "EnvironmentName" appended to it)',
            'default': 'PUBAPP'
        },
        'ApplicationTier': {
            'type': CFNString,
            'description': 'Tag value.',
            'default': 'Web'
        },
        'EnvironmentName': {
            'type': CFNString,
            'description': 'Name of Environment',
            'default': 'common'
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
        'VpcId': {
            'type': CFNString,
            'description': 'VPC resources will be created in.'
        },
        'AlbSubnetIds': {
            'type': CFNCommaDelimitedList,
            'description': 'Public subnets that the ALB will be created in.'
        },
        'AlbLogBucket': {
            'type': CFNString,
            'description': 'S3 Bucket where ALB logs will be stored.',
            'default': 'undefined'
        },
        'AcmCertificate': {
            'type': CFNString,
            'description': '(optional) enable the use of SSL by supplying '
                           'a ACM certificate.',
            'default': 'undefined'
        },
        'TargetInstanceIds': {
            'type': list,
            'description': 'List of target instance IDs. Port is assumed '
                           'to be 80.',
            'default': []
        },
        'OnPremiseCidr': {
            'type': CFNString,
            'description': 'On premise CIDR block used in the web Security '
                           'Group.',
            'default': '0.0.0.0/0'
        }
    }

    def create_template(self):
        """Create template (main function called by Stacker)."""
        template = self.template
        variables = self.get_variables()
        template.add_version('2010-09-09')
        template.add_description(TEMPLATE_DESCRIPTION)

        tcp = '6'
        common_tags = {
            'Application': variables['ApplicationName'].ref,
            'Application Tier': variables['ApplicationTier'].ref,
            'Environment': variables['EnvironmentName'].ref,
            'CostCenter': variables['CostCenter'].ref,
            'TechOwner': variables['CostCenter'].ref,
            'TechOwnerEmail': variables['CostCenter'].ref,
        }

    # Conditions
        acm_provided = template.add_condition(
            'ManagementCidrProvided',
            And(
                Not(Equals(variables['AcmCertificate'].ref, '')),
                Not(Equals(variables['AcmCertificate'].ref, 'undefined'))
            )
        )
        acm_not_provided = template.add_condition(
            'ManagementCidrNotProvided',
            Or(
                Equals(variables['AcmCertificate'].ref, ''),
                Equals(variables['AcmCertificate'].ref, 'undefined')
            )
        )
        alb_log_bucket_provided = template.add_condition(
            'AlbLogBucketProvided',
            And(
                Not(Equals(variables['AlbLogBucket'].ref, '')),
                Not(Equals(variables['AlbLogBucket'].ref, 'undefined'))
            )
        )

    # Security Groups
        web_sg = template.add_resource(ec2.SecurityGroup(
            'WebSecurityGroup',
            GroupName=Sub(
                '${CustomerName}-${ApplicationName}-web-${EnvironmentName}'
            ),
            GroupDescription='Web Server Security Group',
            VpcId=variables['VpcId'].ref
        ))
        template.add_output(Output(
            'WebSecurityGroup',
            Description='Web server Security Group',
            Export=Export(Sub('${AWS::StackName}-WebSecurityGroup')),
            Value=Ref(web_sg)
        ))

        alb_sg = template.add_resource(ec2.SecurityGroup(
            'AlbSecurityGroup',
            GroupName=Sub(
                '${CustomerName}-${ApplicationName}-alb-${EnvironmentName}'
            ),
            GroupDescription='ALB Security Group',
            VpcId=variables['VpcId'].ref,
            SecurityGroupIngress=[
                ec2.SecurityGroupRule(
                    Description='Default HTTP',
                    IpProtocol=tcp,
                    FromPort='80',
                    ToPort='80',
                    CidrIp='0.0.0.0/0'
                ),
                ec2.SecurityGroupRule(
                    Description='Default HTTPS',
                    IpProtocol=tcp,
                    FromPort='443',
                    ToPort='443',
                    CidrIp='0.0.0.0/0'
                )
            ],
            SecurityGroupEgress=[
                ec2.SecurityGroupRule(
                    Description='Default Egress',
                    IpProtocol='-1',
                    CidrIp='0.0.0.0/0'
                )
            ]
        ))
        template.add_output(Output(
            'AlbSecurityGroup',
            Description='Application Load Balancer Security Group',
            Export=Export(Sub('${AWS::StackName}-AlbSecurityGroup')),
            Value=Ref(alb_sg)
        ))

        template.add_resource(ec2.SecurityGroupIngress(
            'WebAlbSecurityGroupRule80',
            GroupId=Ref(web_sg),
            Description='HTTP from ALB',
            SourceSecurityGroupId=Ref(alb_sg),
            IpProtocol=tcp,  # tcp
            FromPort='80',
            ToPort='80'
        ))
        template.add_resource(ec2.SecurityGroupIngress(
            'WebAlbSecurityGroupRule443',
            GroupId=Ref(web_sg),
            Description='HTTPS from ALB',
            SourceSecurityGroupId=Ref(alb_sg),
            IpProtocol=tcp,
            FromPort='443',
            ToPort='443'
        ))
        template.add_resource(ec2.SecurityGroupIngress(
            'WebOnPremSecurityGroupRule80',
            GroupId=Ref(web_sg),
            Description='HTTP from On-Prem',
            CidrIp=variables['OnPremiseCidr'].ref,
            IpProtocol=tcp,
            FromPort='80',
            ToPort='80'
        ))
        template.add_resource(ec2.SecurityGroupIngress(
            'WebOnPremSecurityGroupRule443',
            GroupId=Ref(web_sg),
            Description='HTTPS from On-Prem',
            CidrIp=variables['OnPremiseCidr'].ref,
            IpProtocol=tcp,
            FromPort='443',
            ToPort='443'
        ))
        template.add_resource(ec2.SecurityGroupIngress(
            'WebOnPremSecurityGroupRule3389',
            GroupId=Ref(web_sg),
            Description='RDP from On-Prem',
            CidrIp=variables['OnPremiseCidr'].ref,
            IpProtocol=tcp,
            FromPort='3389',
            ToPort='3389'
        ))

    # Application Load Balancer
        alb_attributes = [
            elbv2.LoadBalancerAttributes(
                Key='idle_timeout.timeout_seconds',
                Value='4000'  # default 60 can be a value from 1-4000
            ), If(
                alb_log_bucket_provided,
                elbv2.LoadBalancerAttributes(
                    Key='access_logs.s3.enabled',
                    Value='true'
                ),
                Ref('AWS::NoValue')
            ), If(
                alb_log_bucket_provided,
                elbv2.LoadBalancerAttributes(
                    Key='access_logs.s3.bucket',
                    Value=variables['AlbLogBucket'].ref
                ),
                Ref('AWS::NoValue')
            )
        ]

        alb = template.add_resource(elbv2.LoadBalancer(
            'Alb',
            Name=Sub(
                '${CustomerName}-${ApplicationName}-alb-${EnvironmentName}'
            ),
            Type='application',
            Scheme='internet-facing',
            Subnets=variables['AlbSubnetIds'].ref,
            SecurityGroups=[Ref(alb_sg)],
            LoadBalancerAttributes=alb_attributes,
            Tags=Tags(
                Name=Sub(
                    '${CustomerName}-${ApplicationName}-alb-'
                    '${EnvironmentName}'
                ), **common_tags
            )
        ))
        template.add_output(Output(
            'Alb',
            Description='Application Load Balancer Arn.',
            Export=Export(Sub('${AWS::StackName}-Alb')),
            Value=Ref(alb)
        ))
        template.add_output(Output(
            'AlbDnsName',
            Description='Application Load Balancer DNSName.',
            Export=Export(Sub(
                '${AWS::StackName}-AlbDnsName'
            )),
            Value=GetAtt(alb, 'DNSName')
        ))
        template.add_output(Output(
            'AlbName',
            Description='Application Load Balancer Name.',
            Export=Export(Sub(
                '${AWS::StackName}-AlbName'
            )),
            Value=GetAtt(alb, 'LoadBalancerName')
        ))
        template.add_output(Output(
            'AlbLoadBalancerFullName',
            Description='Application Load Balancer LoadBalancerFullName.',
            Export=Export(Sub(
                '${AWS::StackName}-AlbLoadBalancerFullName'
            )),
            Value=GetAtt(alb, 'LoadBalancerFullName')
        ))

    # Target Group
        tg = template.add_resource(elbv2.TargetGroup(
            'TargetGroup',
            DependsOn=alb.title,
            Name=Sub('${ApplicationName}-${EnvironmentName}'),
            Protocol='HTTP',
            Port=80,
            HealthCheckIntervalSeconds=10,
            HealthCheckPath='/',
            HealthCheckPort=80,
            HealthCheckProtocol='HTTP',
            HealthCheckTimeoutSeconds=5,
            HealthyThresholdCount=2,
            UnhealthyThresholdCount=2,
            Matcher=elbv2.Matcher(
                HttpCode='200'
            ),
            VpcId=variables['VpcId'].ref,
            TargetType='instance',
            Targets=self.tg_instance_targets,
            Tags=Tags(
                Name=Sub(
                    '${CustomerName}-${ApplicationName}-target-group-'
                    '${EnvironmentName}'
                ), **common_tags
            )
        ))
        template.add_output(Output(
            'TargetGroup',
            Description='Target Group Arn.',
            Export=Export(Sub('${AWS::StackName}-TargetGroup')),
            Value=Ref(tg)
        ))
        template.add_output(Output(
            'TargetGroupName',
            Description='Target Group Name.',
            Export=Export(Sub(
                '${AWS::StackName}-TargetGroupName'
            )),
            Value=GetAtt(tg, 'TargetGroupName')
        ))
        template.add_output(Output(
            'TargetGroupFullName',
            Description='Target Group FullName.',
            Export=Export(Sub(
                '${AWS::StackName}-TargetGroupFullName'
            )),
            Value=GetAtt(tg, 'TargetGroupFullName')
        ))

    # Listeners
        template.add_resource(elbv2.Listener(
            'HttpListener',
            Condition=acm_not_provided,
            LoadBalancerArn=Ref(alb),
            Port=80,
            Protocol='HTTP',
            DefaultActions=[elbv2.Action(
                TargetGroupArn=Ref(tg),
                Type='forward'
            )]
        ))
        template.add_resource(elbv2.Listener(
            'HttpsListener',
            Condition=acm_provided,
            LoadBalancerArn=Ref(alb),
            Port=443,
            Protocol='HTTPS',
            DefaultActions=[elbv2.Action(
                TargetGroupArn=Ref(tg),
                Type='forward'
            )],
            Certificates=[elbv2.Certificate(
                CertificateArn=variables['AcmCertificate'].ref
            )],
            SslPolicy='ELBSecurityPolicy-TLS-1-2-2017-01'
        ))
        template.add_resource(elbv2.Listener(
            'HttpListenerRedirect',
            Condition=acm_provided,
            LoadBalancerArn=Ref(alb),
            Port=80,
            Protocol='HTTP',
            DefaultActions=[elbv2.Action(
                Type='redirect',
                RedirectConfig=elbv2.RedirectConfig(
                    Host='#{host}',
                    Path='/#{path}',
                    Port='443',
                    Protocol='HTTPS',
                    Query='#{query}',
                    StatusCode='HTTP_301'
                )
            )]
        ))

    @property
    def tg_instance_targets(self):
        """Generates list of Target Group targets."""
        variables = self.get_variables()
        result = []

        if not variables['TargetInstanceIds']:
            return [Ref('AWS::NoValue')]

        for target in variables['TargetInstanceIds']:
            result.append(elbv2.TargetDescription(
                Id=target,
                Port=80
            ))

        return result


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    print(BlueprintClass('test', Context({'namespace': 'test'})).to_json({
        'VpcId': 'vpc-xxxx',
        'AlbSubnetIds': 'sub-xxxx,sub-yyyy',
        'TargetInstanceIds': ['i-xxxx']
    }))
