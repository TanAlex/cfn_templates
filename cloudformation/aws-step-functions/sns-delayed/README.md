# Readme

https://alestic.com/2019/05/aws-delayed-sns-step-functions/

git clone git@github.com:alestic/aws-sns-delayed.git
cd aws-sns-delayed

email=YOUREMAIL@example.com
stack_name=sns-delayed-demo

stack_parameters="NotificationEmail=$email"
aws cloudformation deploy \
  --stack-name "$stack_name" \
  --template-file template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides "$stack_parameters"

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

execution_input='{
  "delay_seconds": 60,
  "subject": "Test message delayed through AWS Step Functions",
  "message": "hello, world"
}'

aws stepfunctions start-execution \
  --state-machine-arn "$state_machine" \
  --input "$execution_input"