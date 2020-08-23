https://docs.aws.amazon.com/codebuild/latest/userguide/sample-bitbucket-pull-request.html

## Filter Bitbucket webhook events (AWS CloudFormation)
To use an AWS CloudFormation template to filter webhook events, use the AWS CodeBuild project's FilterGroups property. The following YAML-formatted portion of an AWS CloudFormation template creates two filter groups. Together, they trigger a build when one or both evaluate to true:

The first filter group specifies pull requests are created or updated on branches with Git reference names that match the regular expression ^refs/heads/main$ by a Bitbucket user who does not have account ID 12345.

The second filter group specifies push requests are created on branches with Git reference names that match the regular expression ^refs/heads/.*.

The third filter group specifies a push request with a head commit message matching the regular expression \[CodeBuild\].

```CodeBuildProject:
  Type: AWS::CodeBuild::Project
  Properties:
    Name: MyProject
    ServiceRole: service-role
    Artifacts:
      Type: NO_ARTIFACTS
    Environment:
      Type: LINUX_CONTAINER
      ComputeType: BUILD_GENERAL1_SMALL
      Image: aws/codebuild/standard:4.0
    Source:
      Type: BITBUCKET
      Location: source-location
    Triggers:
      Webhook: true
      FilterGroups:
        - - Type: EVENT
            Pattern: PULL_REQUEST_CREATED,PULL_REQUEST_UPDATED
          - Type: BASE_REF
            Pattern: ^refs/heads/main$
            ExcludeMatchedPattern: false
          - Type: ACTOR_ACCOUNT_ID
            Pattern: 12345
            ExcludeMatchedPattern: true
        - - Type: EVENT
            Pattern: PUSH
          - Type: HEAD_REF
            Pattern: ^refs/heads/.*
        - - Type: EVENT
            Pattern: PUSH
          - Type: COMMIT_MESSAGE
          - Pattern: \[CodeBuild\]
```