#!/usr/bin/env python
"""Stacker module for creating a RDS instance."""
from __future__ import print_function
from collections import OrderedDict
import copy
from os.path import dirname, realpath
import sys

from troposphere import (
    Equals, FindInMap, GetAtt, If, Join, Not, Output, Ref, Tags, cloudwatch,
    ec2, rds, Or
)

from stacker.blueprints.base import Blueprint, resolve_variable
from stacker.variables import Variable
from stacker.blueprints.variables.types import (
    CFNCommaDelimitedList, CFNNumber, CFNString, EC2VPCId
)


class RdsInstance(Blueprint):
    """Extends Stacker Blueprint class."""

    VARIABLES = {
        'ApplicationName': {
            'type': CFNString,
            'description': 'Name of application for which database will be '
                           'used',
        },
        'EnvironmentName': {
            'type': CFNString,
            'default': 'production',
            'description': 'Name of Environment',
        },
        'VpcId': {
            'type': EC2VPCId,
            'description': 'VPC ID',
        },
        'AllowMajorVersionUpgrade': {
            'type': CFNString,
            'default': 'false',
            'description': 'Enable automatic major version upgrades  - '
                           'true or false',
            'allowed_values': ['true', 'false'],
        },
        'MultiAZ': {
            'type': CFNString,
            'description': 'MultiAZ - true or false',
            'allowed_values': ['true', 'false'],
        },
        'Encrypted': {
            'type': CFNString,
            'description': 'Encrypted Volume at rest - true or false',
            'allowed_values': ['true', 'false'],
        },
        'RdsAllocatedStorage': {
            'type': CFNNumber,
            'default': '300',
            'description': 'Storage to create for RDS databases (GB)',
            'max_value': '3072',
            'min_value': '5',
        },
        'AutoMinorVersionUpgrade': {
            'type': CFNString,
            'default': 'true',
            'description': 'Enable automatic minor version upgrades - '
                           'true or false',
            'allowed_values': ['true', 'false'],
        },
        'RdsEngineType': {
            'type': CFNString,
            'description': 'Engine type to use for RDS instance',
            'allowed_values': [
                'mssql',
                'mssql-2014',
                'mssql-2016',
                'mssql-web-2012',
                'mssql-web-2014',
                'mssql-web-2016',
                'mysql',
                'maria',
                'postgres'],
        },
        'KmsKey': {
            'type': CFNString,
            'default': '',
            'description': 'ARN for the AWS Key Management Service key - '
                           'Blank uses default KMS key or NO KMS key if '
                           'Unencrypted',
        },
        'ParameterGroupName': {
            'type': CFNString,
            'default': '',
            'description': 'Optional RDS parameter group name to use',
        },
        'RdsInstanceIdentifier': {
            'type': CFNString,
            'default': 'undefined',
            'description': 'Optional overrides default Identifier name'
        },
        'RdsInstanceClass': {
            'type': CFNString,
            'default': 'db.m3.large',
            'description': 'Instance type to use for RDS instance'
        },
        'DBPassword': {
            'type': CFNString,
            'no_echo': True,
            'description': 'Password for the administrative user',
        },
        'DBUsername': {
            'type': CFNString,
            'description': 'Master Username for RDS instance',
        },
        'DBSubnetGroupName': {
            'type': CFNString,
            'description': 'DB Subnet Group',
        },
        'BackupRetentionDays': {
            'type': CFNNumber,
            'default': '7',
            'description': 'Number of days to retain backups (1-35)',
            'max_value': '35',
            'min_value': '1',
        },
        'VPNSecurityGroup': {
            'type': CFNString,
            'description': 'VPN Security Group ID'
                           'NOTE: Only enable this to allow RDS access '
                           'over VPN connection.',
            'default': '',
        },
        'SNSTopic': {
            'description': '(Optional) SNS Topic (or list of topics) to '
                           'associate with CloudWatch alarms.',
            'type': CFNCommaDelimitedList,
            'default': '',
        },
        'CpuEvaluationPeriods': {
            'description': 'Number of periods to evaluate with base threshold',
            'type': CFNString,
            'default': '2',
        },
        'CpuComparisonOperator': {
            'description': 'Comparison operator type',
            'type': CFNString,
            'default': 'GreaterThanOrEqualToThreshold',
            'allowed_values': ['GreaterThanOrEqualToThreshold',
                               'GreaterThanThreshold',
                               'LessThanThreshold',
                               'LessThanOrEqualToThreshold']
        },
        'CpuPeriod': {
            'description': 'Period of time to apply the statistics '
                           '(in seconds)',
            'type': CFNNumber,
            'default': '300',
            'allowed_values': ['60',
                               '300',
                               '600',
                               '900',
                               '1800',
                               '3600']
        },
        'CpuStatistic': {
            'description': 'Statistic type to apply to metric',
            'type': CFNString,
            'default': 'Average',
            'allowed_values': ['Average',
                               'Minimum',
                               'Maximum',
                               'Sum',
                               'SampleCount']
        },
        'CpuThreshold': {
            'description': 'Percentage threshold to alert',
            'type': CFNNumber,
            'default': '95',
            'min_value': '1',
            'max_value': '100'
        },
        'DiskComparisonOperator': {
            'description': 'Comparison operator type',
            'type': CFNString,
            'default': 'LessThanOrEqualToThreshold',
            'allowed_values': ['GreaterThanOrEqualToThreshold',
                               'GreaterThanThreshold',
                               'LessThanThreshold',
                               'LessThanOrEqualToThreshold']
        },
        'DiskEvaluationPeriods': {
            'description': 'Number of periods to evaluate with base threshold',
            'type': CFNString,
            'default': '2'
        },
        'DiskStatistic': {
            'description': 'Statistic type to apply to metric',
            'type': CFNString,
            'default': 'Sum',
            'allowed_values': ['Average',
                               'Minimum',
                               'Maximum',
                               'Sum',
                               'SampleCount']
        },
        'DiskPeriod': {
            'description': 'Period of time to apply the statistics '
                           '(in seconds)',
            'type': CFNNumber,
            'default': '300',
            'allowed_values': ['60',
                               '300',
                               '600',
                               '900',
                               '1800',
                               '3600']
        },
        'DiskThreshold': {
            'description': 'Percentage threshold to alert',
            'type': CFNNumber,
            'default': '150000000000',
            'min_value': '1000000000',
            'max_value': '500000000000'
        },
        'MemoryComparisonOperator': {
            'description': 'Comparison operator type',
            'type': CFNString,
            'default': 'LessThanOrEqualToThreshold',
            'allowed_values': ['GreaterThanOrEqualToThreshold',
                               'GreaterThanThreshold',
                               'LessThanThreshold',
                               'LessThanOrEqualToThreshold']
        },
        'MemoryEvaluationPeriods': {
            'description': 'Number of periods to evaluate with base threshold',
            'type': CFNString,
            'default': '2'
        },
        'MemoryStatistic': {
            'description': 'Statistic type to apply to metric',
            'type': CFNString,
            'default': 'Sum',
            'allowed_values': ['Average',
                               'Minimum',
                               'Maximum',
                               'Sum',
                               'SampleCount']
        },
        'MemoryPeriod': {
            'description': 'Period of time to apply the statistics '
                           '(in seconds)',
            'type': CFNNumber,
            'default': '300',
            'allowed_values': ['60',
                               '300',
                               '600',
                               '900',
                               '1800',
                               '3600']
        },
        'MemoryThreshold': {
            'description': 'Percentage threshold to alert',
            'type': CFNNumber,
            'default': '1000000000',
            'min_value': '0',
            'max_value': '500000000000'
        },
        'RdsSnapshotIdentifier': {
            'description': 'ARN of DB snapshot to restore from',
            'type': CFNString,
            'default': 'undefined'
        },
        'OtherTags': {'type': dict,
                      'default': {}}
    }

    # This will be used in resolve_variables to translate the dictionaries
    # in the config file to CFN parameters in VARIABLES
    PARAMS_TO_ADD = [
        {'var_name': 'OtherTags',
         'var_type': CFNString,
         'description': 'Extra tag value to apply to the volume'}
    ]
    DEFINED_VARIABLES = {}

    def defined_variables(self):
        """Override the blueprint defined_variables function.

        Returns:
            dict: variables defined by the blueprint, including our injected
                dynamic variables

        """
        if self.DEFINED_VARIABLES == {}:
            return copy.deepcopy(getattr(self, "VARIABLES", {}))
        else:
            return self.DEFINED_VARIABLES

    def resolve_variables(self, provided_variables):
        """Override the blueprint resolve_variables function.

        This allows our injection of dynamic variables.
        """
        self.resolved_variables = {}
        variable_dict = dict((var.name, var) for var in provided_variables)
        variable_dict.update(update_var_dict(variable_dict,
                                             self.PARAMS_TO_ADD))
        # Disabling invalid-name check because we didn't choose the var name
        self.DEFINED_VARIABLES = updated_def_variables(  # noqa pylint: disable=C0103
            self.defined_variables(),
            variable_dict,
            self.PARAMS_TO_ADD
        )
        for var_name, var_def in self.DEFINED_VARIABLES.items():
            value = resolve_variable(
                var_name,
                var_def,
                variable_dict.get(var_name),
                self.name
            )
            self.resolved_variables[var_name] = value

    def add_conditions(self):
        """Add conditions to template."""
        template = self.template
        variables = self.get_variables()

        template.add_condition('KmsKeyEnabled',
                               Not(Equals(variables['KmsKey'].ref, '')))

        template.add_condition('CustomParameterGroup',
                               Not(Equals(variables['ParameterGroupName'].ref,
                                          '')))

        template.add_condition('CustomUsername',
                               Not(Equals(variables['DBUsername'].ref,
                                          '')))

        template.add_condition('VpnAccessEnabled',
                               Not(Equals(variables['VPNSecurityGroup'].ref,
                                          '')))

        template.add_condition('SnsTopicSpecified',
                               Not(Equals(Join('', variables['SNSTopic'].ref),
                                          '')))

        template.add_condition(
            'IdentifierSpecified',
            Not(Or(
                Equals(variables['RdsInstanceIdentifier'].ref, 'undefined'),
                Equals(variables['RdsInstanceIdentifier'].ref, '')))
        )

        template.add_condition(
            'SnapshotSpecified',
            Not(Or(
                Equals(variables['RdsSnapshotIdentifier'].ref, 'undefined'),
                Equals(variables['RdsSnapshotIdentifier'].ref, '')))
        )

    def add_mappings(self):
        """Add mappings to template."""
        template = self.template
        variables = self.get_variables()

        template.add_mapping('RdsMap', {
            'maria': {
                'RdsParameterGroupName': 'default.mariadb10.0',
                'RdsMasterUsername': 'root',
                'RdsLicenseModel': 'general-public-license',
                'RdsEngine': 'mariadb',
                'RdsEngineVersion': '10.0.17',
                'RdsPort': '3306'},
            'mssql': {
                'RdsParameterGroupName': 'default.sqlserver-se-11.0',
                'RdsMasterUsername': 'sa',
                'RdsLicenseModel': 'license-included',
                'RdsEngine': 'sqlserver-se',
                'RdsEngineVersion': '11.00.6594.0.v1',
                'RdsPort': '1433'},
            'mssql-2014': {
                'RdsParameterGroupName': 'default.sqlserver-se-12.0',
                'RdsMasterUsername': 'sa',
                'RdsLicenseModel': 'license-included',
                'RdsEngine': 'sqlserver-se',
                'RdsEngineVersion': '12.00.5546.0.v1',
                'RdsPort': '1433'},
            'mssql-2016': {
                'RdsParameterGroupName': 'default.sqlserver-se-13.0',
                'RdsMasterUsername': 'sa',
                'RdsLicenseModel': 'license-included',
                'RdsEngine': 'sqlserver-se',
                'RdsEngineVersion': '13.00.4451.0.v1',
                'RdsPort': '1433',
                'RdsPort2': '1434'},
            'mssql-web-2012': {
                'RdsParameterGroupName': 'default.sqlserver-web-11.0',
                'RdsMasterUsername': 'sa',
                'RdsLicenseModel': 'license-included',
                'RdsEngine': 'sqlserver-web',
                'RdsEngineVersion': '11.00.6594.0.v1',
                'RdsPort': '1433'},
            'mssql-web-2014': {
                'RdsParameterGroupName': 'default.sqlserver-web-12.0',
                'RdsMasterUsername': 'sa',
                'RdsLicenseModel': 'license-included',
                'RdsEngine': 'sqlserver-web',
                'RdsEngineVersion': '12.00.5546.0.v1',
                'RdsPort': '1433'},
            'mssql-web-2016': {
                'RdsParameterGroupName': 'default.sqlserver-web-13.0',
                'RdsMasterUsername': 'sa',
                'RdsLicenseModel': 'license-included',
                'RdsEngine': 'sqlserver-web',
                'RdsEngineVersion': '13.00.4451.0.v1',
                'RdsPort': '1433'},
            'postgres': {
                'RdsParameterGroupName': 'default.postgres9.6',
                'RdsMasterUsername': 'postgres',
                'RdsLicenseModel': 'postgresql-license',
                'RdsEngine': 'postgres',
                'RdsEngineVersion': '9.6.6',
                'RdsPort': '5432'},
            'mysql': {
                'RdsParameterGroupName': 'default.mysql5.7',
                'RdsMasterUsername': 'root',
                'RdsLicenseModel': 'general-public-license',
                'RdsEngine': 'mysql',
                'RdsEngineVersion': '5.7.17',
                'RdsPort': '3306'},
        })
        template.add_output(
            Output(
                'RdsMasterUsername',
                Description='The username for the master username',
                Value=If(
                    'CustomUsername',
                    variables['DBUsername'].ref,
                    FindInMap('RdsMap',
                              variables['RdsEngineType'].ref,
                              'RdsMasterUsername'))
            )
        )

    def add_resources(self):
        """Add resources to template."""
        template = self.template
        variables = self.get_variables()

        additional_tags = {}
        for key in variables['OtherTags']:
            if isinstance(variables['OtherTags'][key], dict):
                tag_name = variables['OtherTags'][key]['Name']
            else:
                tag_name = key
            additional_tags[tag_name] = variables[key].ref

        rdsclientsecuritygroup = template.add_resource(
            ec2.SecurityGroup(
                'RdsClientSecurityGroup',
                VpcId=variables['VpcId'].ref,
                SecurityGroupEgress=[
                    ec2.SecurityGroupRule(
                        IpProtocol='-1',
                        FromPort='0',
                        ToPort='65535',
                        CidrIp='0.0.0.0/0')
                ],
                GroupDescription=Join('-', [variables['ApplicationName'].ref,
                                            'RdsClientSecurityGroup',
                                            variables['EnvironmentName'].ref]),
                Tags=Tags(
                    Name=Join('-', ['rds-clients',
                                    variables['ApplicationName'].ref,
                                    variables['EnvironmentName'].ref]),
                    Environment=variables['EnvironmentName'].ref,
                    Application=variables['ApplicationName'].ref,
                    **additional_tags
                )
            )
        )
        template.add_output(
            Output(
                'RdsClientSecurityGroup',
                Description='The ID of the RDS client security group '
                            'associated with the environment',
                Value=Ref(rdsclientsecuritygroup)
            )
        )

        rdsserversecuritygroup = template.add_resource(
            ec2.SecurityGroup(
                'RdsServerSecurityGroup',
                SecurityGroupIngress=[
                    ec2.SecurityGroupRule(
                        IpProtocol='tcp',
                        FromPort=FindInMap('RdsMap',
                                           variables['RdsEngineType'].ref,
                                           'RdsPort'),
                        ToPort=FindInMap('RdsMap',
                                         variables['RdsEngineType'].ref,
                                         'RdsPort'),
                        SourceSecurityGroupId=Ref(rdsclientsecuritygroup)),
                    ec2.SecurityGroupRule(
                        IpProtocol='tcp',
                        FromPort=FindInMap('RdsMap',
                                           variables['RdsEngineType'].ref,
                                           'RdsPort2'),
                        ToPort=FindInMap('RdsMap',
                                         variables['RdsEngineType'].ref,
                                         'RdsPort2'),
                        SourceSecurityGroupId=Ref(rdsclientsecuritygroup))
                                                
                ],
                VpcId=variables['VpcId'].ref,
                SecurityGroupEgress=[
                    ec2.SecurityGroupRule(
                        IpProtocol='-1',
                        FromPort='0',
                        ToPort='65535',
                        CidrIp='0.0.0.0/0')
                ],
                GroupDescription=Join('-', [variables['ApplicationName'].ref,
                                            'RdsServerSecurityGroup',
                                            variables['EnvironmentName'].ref]),
                Tags=Tags(
                    Name=Join('-', ['rds-server',
                                    variables['ApplicationName'].ref,
                                    variables['EnvironmentName'].ref]),
                    Environment=variables['EnvironmentName'].ref,
                    Application=variables['ApplicationName'].ref,
                    **additional_tags
                )
            )
        )
        template.add_output(
            Output(
                rdsserversecuritygroup.title,
                Description='The ID of the RDS server security group '
                            'associated with the rds',
                Value=Ref(rdsserversecuritygroup)
            )
        )

        template.add_resource(
            ec2.SecurityGroupIngress(
                'VpnSgIngress',
                Condition='VpnAccessEnabled',
                GroupId=Ref(rdsserversecuritygroup),
                IpProtocol='tcp',
                FromPort=FindInMap('RdsMap',
                                   variables['RdsEngineType'].ref,
                                   'RdsPort'),
                ToPort=FindInMap('RdsMap',
                                 variables['RdsEngineType'].ref,
                                 'RdsPort'),
                SourceSecurityGroupId=variables['VPNSecurityGroup'].ref
            )
        )

        rdsdatabaseinstance = template.add_resource(
            rds.DBInstance(
                'RdsDatabaseInstance',
                DBParameterGroupName=If(
                    'CustomParameterGroup',
                    variables['ParameterGroupName'].ref,
                    FindInMap('RdsMap',
                              variables['RdsEngineType'].ref,
                              'RdsParameterGroupName')),
                AllowMajorVersionUpgrade=variables['AllowMajorVersionUpgrade'].ref,  # noqa
                MasterUsername=If(
                    'CustomUsername',
                    variables['DBUsername'].ref,
                    FindInMap('RdsMap',
                              variables['RdsEngineType'].ref,
                              'RdsMasterUsername')),
                LicenseModel=FindInMap('RdsMap',
                                       variables['RdsEngineType'].ref,
                                       'RdsLicenseModel'),
                VPCSecurityGroups=[Ref(rdsserversecuritygroup)],
                Engine=FindInMap('RdsMap',
                                 variables['RdsEngineType'].ref,
                                 'RdsEngine'),
                MultiAZ=variables['MultiAZ'].ref,
                Tags=Tags(
                    Name=Join('-', [variables['ApplicationName'].ref,
                                    variables['EnvironmentName'].ref]),
                    Environment=variables['EnvironmentName'].ref,
                    Application=variables['ApplicationName'].ref,
                    **additional_tags
                ),
                AutoMinorVersionUpgrade=variables['AutoMinorVersionUpgrade'].ref,  # noqa
                PreferredBackupWindow='03:00-04:00',
                AllocatedStorage=variables['RdsAllocatedStorage'].ref,
                DBSubnetGroupName=variables['DBSubnetGroupName'].ref,
                PreferredMaintenanceWindow='sat:06:00-sat:07:00',
                EngineVersion=If('SnapshotSpecified',
                                Ref('AWS::NoValue'),
                                FindInMap('RdsMap',
                                        variables['RdsEngineType'].ref,
                                        'RdsEngineVersion')),
                BackupRetentionPeriod=variables['BackupRetentionDays'].ref,
                StorageType='gp2',
                MasterUserPassword=variables['DBPassword'].ref,
                KmsKeyId=If('KmsKeyEnabled',
                            variables['KmsKey'].ref,
                            Ref('AWS::NoValue')),
                StorageEncrypted=variables['Encrypted'].ref,
                DBInstanceClass=variables['RdsInstanceClass'].ref,
                Port=FindInMap('RdsMap',
                               variables['RdsEngineType'].ref,
                               'RdsPort'),
                DBInstanceIdentifier=If(
                    'IdentifierSpecified',
                    variables['RdsInstanceIdentifier'].ref,
                    Join(
                        '-',
                        [variables['ApplicationName'].ref,
                         variables['EnvironmentName'].ref])),
                DBSnapshotIdentifier=If('SnapshotSpecified',
                                        variables['RdsSnapshotIdentifier'].ref,
                                        Ref('AWS::NoValue'))
            )
        )

        template.add_resource(
            cloudwatch.Alarm(
                'HighCPUAlarm',
                Condition='SnsTopicSpecified',
                ActionsEnabled='true',
                AlarmActions=variables['SNSTopic'].ref,
                AlarmDescription='CPU Utilization Alarm for RDS',
                AlarmName=Join('-', [variables['EnvironmentName'].ref,
                                     'CPUUtilization',
                                     'RDS',
                                     'alarm']),
                ComparisonOperator=variables['CpuComparisonOperator'].ref,
                OKActions=variables['SNSTopic'].ref,
                EvaluationPeriods=variables['CpuEvaluationPeriods'].ref,
                MetricName='CPUUtilization',
                Namespace='AWS/RDS',
                Period=variables['CpuPeriod'].ref,
                Statistic=variables['CpuStatistic'].ref,
                Threshold=variables['CpuThreshold'].ref
            )
        )

        template.add_resource(
            cloudwatch.Alarm(
                'FreeStorageSpace',
                Condition='SnsTopicSpecified',
                ActionsEnabled='true',
                AlarmActions=variables['SNSTopic'].ref,
                AlarmDescription='Disk Space Alarm for RDS',
                AlarmName=Join('-', [variables['EnvironmentName'].ref,
                                     'FreeDiskSpace',
                                     'RDS',
                                     'alarm']),
                ComparisonOperator=variables['DiskComparisonOperator'].ref,
                OKActions=variables['SNSTopic'].ref,
                EvaluationPeriods=variables['DiskEvaluationPeriods'].ref,
                MetricName='FreeStorageSpace',
                Namespace='AWS/RDS',
                Period=variables['DiskPeriod'].ref,
                Statistic=variables['DiskStatistic'].ref,
                Threshold=variables['DiskThreshold'].ref
            )
        )

        template.add_resource(
            cloudwatch.Alarm(
                'FreeableMemory',
                Condition='SnsTopicSpecified',
                ActionsEnabled='true',
                AlarmActions=variables['SNSTopic'].ref,
                AlarmDescription='Free memory Alarm for RDS',
                AlarmName=Join('-', [variables['EnvironmentName'].ref,
                                     'FreeableMemory',
                                     'RDS',
                                     'alarm']),
                ComparisonOperator=variables['MemoryComparisonOperator'].ref,
                OKActions=variables['SNSTopic'].ref,
                EvaluationPeriods=variables['MemoryEvaluationPeriods'].ref,
                MetricName='FreeableMemory',
                Namespace='AWS/RDS',
                Period=variables['MemoryPeriod'].ref,
                Statistic=variables['MemoryStatistic'].ref,
                Threshold=variables['MemoryThreshold'].ref
            )
        )
        template.add_output(
            Output(
                'RdsDatabaseInstance',
                Description='The name of the RDS instance for the environment',
                Value=GetAtt(rdsdatabaseinstance, 'Endpoint.Address')
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.add_conditions()
        self.template.add_version('2010-09-09')
        self.template.add_description("Sturdy Platform - RDS Instance "
                                      "- {0}".format(version()))
        self.add_mappings()
        self.add_resources()


def updated_def_variables(variables, provided_var_dict, params_to_add):
    """Add CFN parameters to template based on the specified lists.

    Example params_to_add list:
        params_to_add = [
            {'var_name': 'OtherTags',
             'var_type': CFNString,
             'description': 'Extra tag value to apply to the instances'},
            {'var_name': 'OtherSGs',
             'var_type': CFNString,
             'description': 'Extra security group to apply to the instances'}
        ]
    """
    for param_to_add in params_to_add:
        if param_to_add['var_name'] in provided_var_dict:
            for key, _value in provided_var_dict[param_to_add['var_name']].value.items():  # noqa pylint: disable=C0301
                variables[key] = {
                    'type': param_to_add['var_type'],
                    'description': param_to_add['description']
                }
    return variables


def update_var_dict(provided_var_dict, params_to_add):
    """Return a dictionary to add to resolve_variables()'s variable_dict."""
    additional_vars = {}
    for param_to_add in params_to_add:
        if param_to_add['var_name'] in provided_var_dict:
            for key, value in provided_var_dict[param_to_add['var_name']].value.items():  # noqa pylint: disable=C0301
                if isinstance(value, (dict, OrderedDict)):
                    additional_vars[key] = Variable(key, dict(value)['Value'])
                else:
                    additional_vars[key] = Variable(key, value)
    return additional_vars


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

    print(RdsInstance('test',
                      Context({'namespace': 'test'}),
                      None).to_json())
