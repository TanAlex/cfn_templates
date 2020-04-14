#ec2.yaml
This is a template for creating Single Box environment using following Parameters based on Single Box Environment Discovery document.

##Required Tags as parameter
- ChefEnvironment
- ChefRunlist
- Name
- Application
- Environment

##Optional Tags as parameter
- CostCenter
- TechOwner
- TechOwnerEmail
  
##Instance Properties as parameter
- KeyPairName
- ImageId
- PrivateSubnetID
- Volume1Size
- Volume2Size
- InstanceType
- SecurityGroupId

##Note
- Some parameter values are set to default which does not change
- Userdata is used from /aws-iac/scripts/chef-userdata/linux/userdata.yaml

Dsicovery Documentation - https://docs.google.com/spreadsheets/d/1crh27tnupltv_nWfFyoTp1xiGIKxjh2YkyhjLEnEaEI/edit#gid=0
