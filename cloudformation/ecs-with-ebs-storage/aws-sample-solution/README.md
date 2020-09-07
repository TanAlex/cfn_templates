ECS Cluster with EBS storage,

https://aws.amazon.com/blogs/compute/amazon-ecs-and-docker-volume-drivers-amazon-ebs/

The ECS LaunchConfig highlight, use REXRAY plugin to connect to EBS
```
#open file descriptor for stderr
exec 2>>/var/log/ecs/ecs-agent-install.log
set -x
#verify that the agent is running
until curl -s http://localhost:51678/v1/metadata
do
	sleep 1
done
#install the Docker volume plugin
docker plugin install rexray/ebs REXRAY_PREEMPT=true EBS_REGION=<AWS_REGION> --grant-all-permissions
#restart the ECS agent
stop ecs 
start ecs
```

Deploy

```
stack_name='rexray-demo'
stack_parameters='KeyName=default-key'
aws cloudformation deploy \
  --stack-name "$stack_name" \
  --template-file cluster.template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides "$stack_parameters"
```

Get Output
./get-outputs.sh  && source < ./get-outputs.sh 

Create Tasks
```
envsubst < mysql-task-definition.template.json > mysql-task-definition.json 

export TaskDefinitionArn=$(aws ecs register-task-definition \
--cli-input-json 'file://mysql-task-definition.json' \
| jq -r .taskDefinition.taskDefinitionArn)

envsubst < mysql-service-definition.template.json > mysql-service-definition.json

export SvcDefinitionArn=$(aws ecs create-service \
--cli-input-json file://mysql-service-definition.json \
| jq -r .service.serviceArn)

```


Clean Up

Drain and Delete Service
```
aws ecs update-service --cluster $ECSClusterName \
--service $SvcDefinitionArn \
--desired-count 0
aws ecs delete-service --cluster $ECSClusterName \
--service $SvcDefinitionArn
```