echo "Region [$AWSRegion]"
echo "Cluster [$ECSClusterName]"
echo "Task Definition [$TaskDefinitionArn]"

TaskArns=$(aws ecs list-tasks --region $AWSRegion \
--cluster $ECSClusterName --query taskArns --output text)
echo "Task ARNs [$TaskArns]"

ContainerInstanceArns=$(aws ecs describe-tasks \
--region $AWSRegion --cluster $ECSClusterName \
--tasks $TaskArns \
--query 'tasks[?taskDefinitionArn==`'$TaskDefinitionArn'`]' \
--query 'tasks[].containerInstanceArn' --output text)
echo "Container Instance ARNs [$ContainerInstanceArns]"

echo "DRAINING Instances"
aws ecs update-container-instances-state --region $AWSRegion \
--cluster $ECSClusterName --container-instances $ContainerInstanceArns \
--status "DRAINING"