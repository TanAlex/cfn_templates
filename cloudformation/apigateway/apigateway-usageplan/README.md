https://medium.com/devtechblogs/three-aws-api-gateway-features-to-manage-and-control-the-invocations-of-its-targets-32af562696b9

https://stackoverflow.com/questions/39910734/can-you-create-usage-plan-with-cloud-formation
UsagePlan:
  Type: 'AWS::ApiGateway::UsagePlan'
  Properties:
    ApiStages:
      - ApiId: !Ref MyRestApi
        Stage: !Ref Prod
    Description: Customer ABCs usage plan
    Quota:
      Limit: 5000
      Period: MONTH
    Throttle:
      BurstLimit: 200
      RateLimit: 100
    UsagePlanName: Plan_ABC

ApiKey:
  Type: 'AWS::ApiGateway::ApiKey'
  Properties:
    Name: TestApiKey
    Description: CloudFormation API Key V1
    Enabled: 'true'

UsagePlanKey:
  Type: 'AWS::ApiGateway::UsagePlanKey'
  Properties:
    KeyId: !Ref ApiKey
    KeyType: API_KEY
    UsagePlanId: !Ref UsagePlan

https://aws.amazon.com/blogs/aws/new-usage-plans-for-amazon-api-gateway/