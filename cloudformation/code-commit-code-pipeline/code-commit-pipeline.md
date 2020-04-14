# README

ref: https://github.com/awslabs/aws-well-architected-labs.git 

Create 

AWS::CodeCommit::Repository
AWS::ECR::Repository

Role for CW PR EventRuleRole
```
  PREventRuleRole: 
    Type: AWS::IAM::Role
```

PR Event Rule
```
  PREventRule:
    Type: "AWS::Events::Rule"
    Properties:
      Name: !Join [ '-', [ !Ref ResourceName, 'pr'  ] ]
      Description: "Trigger notifications based on CodeCommit Pull Requests"
      EventPattern:
        source:
          - "aws.codecommit"
        detail-type:
          - "CodeCommit Pull Request State Change"
        resources:
          - !GetAtt AppRepository.Arn
        detail:
          event:
            - "pullRequestSourceBranchUpdated"
            - "pullRequestCreated"
      State: "ENABLED"
      Targets:
        - Arn: !GetAtt LambdaPR.Arn
          Id: !Join [ '-', [ !Ref ResourceName, 'pr'  ] ]
```

When PR -> trigger the lambda to run codepipeline

```
          codecommit_client = boto3.client('codecommit')
          ssm = boto3.client('ssm')
          codepipeline = boto3.client('codepipeline')
...
...
          codepipeline.start_pipeline_execution(
            name=pipeline,
          )
```