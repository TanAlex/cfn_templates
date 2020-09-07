# ECS Cluster with EBS storage

https://aws.amazon.com/blogs/compute/amazon-ecs-and-docker-volume-drivers-amazon-ebs/

## Validate Template

```
aws cloudformation validate-template --template-body file://cluster.template.yaml
```

## Setup environment
```
sso-login your-lab-account
export AWS_DEFAULT_REGION=${your_default_region} # something like us-west-1 etc.
```


## Deploy Template
Create a SSH KeyPair and name it default-key

```
stack_name='ecs-ebs-test'
stack_parameters='KeyName=default-key'
aws cloudformation deploy \
  --stack-name "$stack_name" \
  --template-file cluster.template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides "$stack_parameters"
```

Use CloudWatch to check container's log  
There should be lines like these

```
2020-09-06T15:21:59.662-07:00	Jenkins initial setup is required. An admin user has been created and a password generated.

2020-09-06T15:21:59.662-07:00	Please use the following password to proceed to installation:

2020-09-06T15:21:59.662-07:00	f544f14314944d65aa3497d74ddbdad5

2020-09-06T15:21:59.662-07:00	This may also be found at: /var/jenkins_home/secrets/initialAdminPassword
```
Or you can `docker exec` into the docker container  
then use this to get the initial Admin password
```
cat /var/jenkins_home/secrets/initialAdminPassword
```



### When you updated the stack, use this to update
```
stack_name='ecs-ebs-test'
stack_parameters='ParameterKey=KeyName,ParameterValue=default-key'
aws cloudformation update-stack \
  --stack-name "$stack_name" \
  --template-body file://cluster.template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter "$stack_parameters"
```


### Things learned

* When the ecs-task uses 'awsvpc' network type, then neither `docker ps` or `docker inspect` will show that docker container's IP. You can't use 'hostPort' in the task's containerDefinition too because `awsvpc` implies the 'hostport' and 'container port' are the same because it's just associated with a dedicate ENI

* The original article uses only one public subnet. The docker container uses 'awsvpc' network type and disabled public-IP-assignment, so the container has only private IP. Because there is no NAT Gateway so the container can accept connections and serve well but it can't reach Internet inside the container.
The Solution is to create a separated private network with NAT and separate the LB and the Instances. Put all instances in private network and they use NAT Gateway to go out.

* NLB can't not associate with an SG. Only ALB and ELB can. So we have to use IP Cidr Range for the source of all the ECS insances' SG. If we use ALB, we can just put ALB in the internet-facing SG and use that as the source of our internal SG.

* The ECS' ASG LaunchConfiguration has `AssociatePublicIpAddress` setting, it was set to true, so all the ECS' instances have public IP even they are using private subnet. Have to change it to 'false'. NOTE: when you change this and update stack, the instances will be terminated and ASG will bring up new instances with no pub-IPs
```
  ContainerInstances:
    Type: AWS::AutoScaling::LaunchConfiguration
    Properties:
      ImageId:
        Ref: ECSAMI
      InstanceType:
        Ref: InstanceType
      IamInstanceProfile:
        Ref: EC2InstanceProfile
      KeyName:
        Ref: KeyName
      AssociatePublicIpAddress: false
```

* The volumn is created automatically, because it uses `Autoprovision: true`  
Can set it to false if you already have EBS volumes to use or prefer to create it manually

```
 Volumes:
        - Name: rexray-vol
          DockerVolumeConfiguration:
            Autoprovision: true
            Scope: shared
            Driver: rexray/ebs
            DriverOpts:
              Volumetype: gp2
              Size: 200
```