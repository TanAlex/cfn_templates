# CFN Stacks CLI
```

## validate template
aws cloudformation validate-template --template-body file://sampletemplate.json

aws cloudformation create-stack \
  --stack-name MyNetworkStack \
  --template-body file://my-network-template.yaml

aws cloudformation describe-stack --stack-name MyNetworkStack

aws cloudformation update-stack \
  --stack-name MyNetworkStack \
  --template-body file://bad-network-template.yaml

aws ec2 describe-vpcs --filters "Name=tag:Name,Values=MyVPC"

# Get all AWS Linux AMI
$ regions=$(aws ec2 describe-regions --query "Regions[].RegionName" --output text)
$ for region in $regions; do ami=$(aws --region $region ec2 describe-images --filters "Name=name,Values=amzn2-ami-hvm-2.0.20200304.0-x86_64-gp2" --query "Images[0].ImageId" --output "text"); printf "'$region':\n  AMI: '$ami'\n"; done

# Get all ecs AMI
$ regions=$(aws ec2 describe-regions --query "Regions[].RegionName" --output text)
$ for region in $regions; do ami=$(aws --region $region ec2 describe-images --filters "Name=name,Values=amzn2-ami-ecs-hvm-2.0.20200319-x86_64-ebs" --query "Images[0].ImageId" --output "text"); printf "'$region':\n  ECSAMI: '$ami'\n"; done
```



### Deploy
```
stack_parameters="NotificationEmail=$email"
aws cloudformation deploy \
  --stack-name "$stack_name" \
  --template-file template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides "$stack_parameters"
```

### Get output
```
state_machine=$(aws cloudformation describe-stacks \
  --stack-name "$stack_name" \
  --output text \
  --query 'Stacks[][Outputs][][?OutputKey==`StepFunctionsStateMachine`][OutputValue]')
echo state_machine=$state_machine

sns_topic=$(aws cloudformation describe-stacks \
  --stack-name "$stack_name" \
  --output text \
  --query 'Stacks[][Outputs][][?OutputKey==`SNSTopic`][OutputValue]')
echo sns_topic=$sns_topic
```

### Post SNS message
```
aws sns publish \
  --topic-arn "$sns_topic" \
  --subject "Test message published directly to SNS topic" \
  --message "hello, world"
```

### List AWS Accounts in AWS Organization

```
aws organizations list-accounts \
  --output text \
  --query 'Accounts[?Status==`ACTIVE`][Status,JoinedTimestamp,Id,Email,Name]' |
  sort |
  cut -f2- |
  column -t -n -e -s$'\cI'
```

### create-stack and wait
```
aws cloudformation create-stack --stack-name example --template-body file://template.yml --capabilities CAPABILITY_IAM
aws cloudformation wait stack-create-complete --stack-name example
```
