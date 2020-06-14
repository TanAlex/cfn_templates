https://github.com/linuxacademy/la-aws-security_specialty/tree/master/Enabling-VPC-Flow-Logs-with-Automation

- lambda_function.py creates VPC Flow Logs for the VPC ID in the event
- event-pattern.json is the CloudWatch Rule event pattern for monitoring the CreateVpc API call.
- test-event.json is a sample CloudTrail event that can be used with the Lambda function, as it contains the VPC ID


Event Pattern
```
{
    "source": [
        "aws.ec2"
    ],
    "detail-type": [
        "AWS API Call via CloudTrail"
    ],
    "detail": {
        "eventSource": [
            "ec2.amazonaws.com"
        ],
        "eventName": [
            "CreateVpc"
        ]
    }
}
```

Test Event:
```{
    "version": "0",
    "id": "e3f9c65c-6b72-3ce4-b1f3-20494cbc87e0",
    "detail-type": "AWS API Call via CloudTrail",
    "source": "aws.ec2",
    "account": "111111111111",
    "time": "2018-06-18T15:33:07Z",
    "region": "us-east-1",
    "resources": [],
    "detail": {
      "eventVersion": "1.05",
      "userIdentity": {
        "type": "Root",
        "principalId": "111111111111",
        "arn": "arn:aws:iam::111111111111:root",
        "accountId": "111111111111",
        "accessKeyId": "...",
        "sessionContext": {
          "attributes": {
            "mfaAuthenticated": "false",
            "creationDate": "2018-06-18T14:13:11Z"
          }
        },
        "invokedBy": "signin.amazonaws.com"
      },
      "eventTime": "2018-06-18T15:33:07Z",
      "eventSource": "ec2.amazonaws.com",
      "eventName": "CreateVpc",
      "awsRegion": "us-east-1",
      "sourceIPAddress": "73.125.25.100",
      "userAgent": "signin.amazonaws.com",
      "requestParameters": {
        "cidrBlock": "10.0.0.0/16",
        "instanceTenancy": "default"
      },
      "responseElements": {
        "requestId": "ee1f6203-3e40-4669-a50b-17c52abc69b7",
        "vpc": {
          "vpcId": "vpc-0a71e831cb5152c43",
          "state": "pending",
          "cidrBlock": "10.0.0.0/16",
          "cidrBlockAssociationSet": {
            "items": [
              {
                "cidrBlock": "10.0.0.0/16",
                "associationId": "vpc-cidr-assoc-07ba205e048b7798a",
                "cidrBlockState": {
                  "state": "associated"
                }
              }
            ]
          },
          "ipv6CidrBlockAssociationSet": {},
          "dhcpOptionsId": "dopt-c0bf6fbb",
          "instanceTenancy": "default",
          "tagSet": {},
          "isDefault": false
        }
      },
      "requestID": "ee1f6203-3e40-4669-a50b-17c52abc69b7",
      "eventID": "9be08716-256d-4286-9378-8137d661109b",
      "eventType": "AwsApiCall"
    }
  }
```

Lambda
```
import boto3
import os


def lambda_handler(event, context):
    '''
    Extract the VPC ID from the event and enable VPC Flow Logs.
    '''

    try:
        vpc_id = event['detail']['responseElements']['vpc']['vpcId']

        print('VPC: ' + vpc_id)

        ec2_client = boto3.client('ec2')

        response = ec2_client.describe_flow_logs(
            Filter=[
                {
                    'Name': 'resource-id',
                    'Values': [
                        vpc_id,
                    ]
                },
            ],
        )

        if len(response[u'FlowLogs']) != 0:
            print('VPC Flow Logs are ENABLED')
        else:
            print('VPC Flow Logs are DISABLED')

            print('FLOWLOGS_GROUP_NAME: ' + os.environ['FLOWLOGS_GROUP_NAME'])
            print('ROLE_ARN: ' + os.environ['ROLE_ARN'])

            response = ec2_client.create_flow_logs(
                ResourceIds=[vpc_id],
                ResourceType='VPC',
                TrafficType='ALL',
                LogGroupName=os.environ['FLOWLOGS_GROUP_NAME'],
                DeliverLogsPermissionArn=os.environ['ROLE_ARN'],
            )

            print('Created Flow Logs: ' + response['FlowLogIds'][0])

    except Exception as e:
        print('Error - reason "%s"' % str(e))
```