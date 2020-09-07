# README

define CW Agent's config in SSM
```
  ECSCloudWatchParameter:
    Type: AWS::SSM::Parameter
    Properties:
      Description: ECS
      Name: !Sub "AmazonCloudWatch-${ECSCluster}-ECS"
      Type: String
      Value: !Sub |
        {
          "logs": {
```

Then use `ssm:${ECSCloudWatchParameter}` to refer to it
```
02_enable_cloudwatch_agent:
              command: !Sub /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c ssm:${ECSCloudWatchParameter} -s
```