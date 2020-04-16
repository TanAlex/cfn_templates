https://github.com/aws-quickstart/quickstart-examples/tree/master/samples/cloudformation-codebuild-container

custom resource lambda calls codebuild based on a docker image


```
  CodeBuildProject:
    Type: AWS::CodeBuild::Project
    DependsOn: CopyZips
    Properties:
      Description: Builds a docker container and pushes container images to ECR
      ServiceRole: !GetAtt 'CodeBuildRole.Arn'
      Artifacts:
        Type: no_artifacts
      Environment:
        Type: LINUX_CONTAINER
        ComputeType: BUILD_GENERAL1_SMALL
        Image: "aws/codebuild/docker:17.09.0"  # <==== where you define the image
        PrivilegedMode: True
```