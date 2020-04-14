# RDS

## Deployment

Use one of the following sample configurations as a template for using this blueprint in your repository (updating all TBD values, repo tag, etc)

### Subnet Group in Common Environment

Subnet Group config:
```
namespace: ${namespace}
stacker_bucket: ${stacker_bucket_name}

package_sources:
  git:
    - uri: git@bitbucket.org:nbdev/sturdy-platform-infrastructure.git
      tag: v1.2.0
      paths:
        - stacker_platform_modules/rds

stacks:
  - name: rds-subnet-TBD
    class_path: rds_blueprints.rds_subnet.RdsSubnet
    variables:
      EnvironmentName: ${environment}
      PriSubnets: ${rxref core-vpc::PriSubnet1},${rxref core-vpc::PriSubnet2}
```

RDS instance config:
```
namespace: ${namespace}
stacker_bucket: ${stacker_bucket_name}

package_sources:
  git:
    - uri: git@bitbucket.org:nbdev/sturdy-platform-infrastructure.git
      tag: v1.2.0
      paths:
        - stacker_platform_modules/rds

stacks:
  - name: rds-instance-TBD
    class_path: rds_blueprints.rds_instance.RdsInstance
    variables:
      EnvironmentName: ${environment}
      ApplicationName: TBD
      DBPassword: ${ssmstore REGION@PARAMETERNAME} # e.g. ${ssmstore us-west-2@prod.webdb.password}
      RdsAllocatedStorage: 300
      RdsEngineType: mysql
      RdsInstanceClass: db.m3.large
      MultiAZ: 'true'
      Encrypted: 'false'
      VpcId: ${xref ${customer}-common-core-vpc::VPC}
      DBSubnetGroupName: ${xref ${customer}-common-rds-subnet::DBSubnetGroup}
```

### Single Environment

```
namespace: ${namespace}
stacker_bucket: ${stacker_bucket_name}

package_sources:
  git:
    - uri: git@bitbucket.org:nbdev/sturdy-platform-infrastructure.git
      tag: v1.2.0
      paths:
        - stacker_platform_modules/rds

stacks:
  - name: rds-subnet-TBD
    class_path: rds_blueprints.rds_subnet.RdsSubnet
    variables:
      EnvironmentName: ${environment}
      PriSubnets: ${xref ${customer}-common-core-vpc::PriSubnet1},${xref ${customer}-common-core-vpc::PriSubnet2}
  - name: rds-instance-TBD
    class_path: rds_blueprints.rds_instance.RdsInstance
    variables:
      EnvironmentName: ${environment}
      ApplicationName: TBD
      DBPassword: ${ssmstore REGION@PARAMETERNAME} # e.g. ${ssmstore us-west-2@prod.webdb.password}
      RdsAllocatedStorage: 300
      RdsEngineType: mysql
      RdsInstanceClass: db.m3.large
      MultiAZ: 'true'
      Encrypted: 'false'
      VpcId: ${xref ${customer}-common-core-vpc::VPC}
      DBSubnetGroupName: ${output rds-subnet-TBD::DBSubnetGroup}
```
