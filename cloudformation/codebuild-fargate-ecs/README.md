# README

Ref: https://github.com/aws-samples/aws-container-devsecops-workshop.git

Define:

ECR repo
ECS cluster
LB with listener and target-group
ECS service associate to target-group
SecurityGroup for LB and ECS service

Tasks 
  Task role and policy
  Task Execution role
  Task definition AWS::ECS::TaskDefinition
  AWS::Logs::LogGroup for tasks



CodeBuild::Project

CodeBuildStarter: a lambda custom-resource to trigger CodeBuild 

```
          codebuild_client = boto3.client('codebuild')

          def handler(event, context):
              try:
                  if event['RequestType'] == 'Create':
                      response = codebuild_client.start_build(
                        projectName=event['ResourceProperties']['ProjectName']
                      )
                      send(event, context, "SUCCESS")
                  elif event['RequestType'] == 'Update':
                      response = codebuild_client.start_build(
                        projectName=event['ResourceProperties']['ProjectName']
                      )
                      send(event, context, "SUCCESS")
                  elif event['RequestType'] == 'Delete':
                      send(event, context, "SUCCESS")
                  else:
                      send(event, context, "FAILED")
              except:
                  send(event, context, "FAILED")
```

Use this to trigger the lambda to build
```

  CodeBuildStarter:
    Type: Custom::CodeBuildStarter
    Properties:
        ServiceToken: !GetAtt CodeBuildStarterLambda.Arn
        ProjectName: !Ref AnchoreCodeBuild
```

