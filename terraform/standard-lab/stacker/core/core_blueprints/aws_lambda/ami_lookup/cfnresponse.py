"""Vendored cfnresponse from AWS.

Retrieved from:
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-lambda-function-code.html

Python2.7 version adapted to py2/3 compatibility w/ slight style tweaks.

Original copyright notice:

Copyright 2016 Amazon Web Services, Inc. or its affiliates.
All Rights Reserved.
This file is licensed to you under the AWS Customer Agreement (the "License").
You may not use this file except in compliance with the License.
A copy of the License is located at http://aws.amazon.com/agreement/ .
This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS
OF ANY KIND, express or implied.
See the License for the specific language governing permissions and limitations
under the License.
"""
from __future__ import print_function

import json
from botocore.vendored import requests

SUCCESS = "SUCCESS"
FAILED = "FAILED"


def send(event, context, responseStatus, responseData, physicalResourceId=None,  # noqa pylint: disable=invalid-name,too-many-arguments
         noEcho=False):
    """Send response to CFN."""
    responseurl = event['responseurl']

    print(responseurl)

    responsebody = {}
    responsebody['Status'] = responseStatus
    responsebody['Reason'] = 'See the details in CloudWatch Log Stream: ' + context.log_stream_name  # noqa pylint: disable=line-too-long
    responsebody['PhysicalResourceId'] = physicalResourceId or context.log_stream_name  # noqa
    responsebody['StackId'] = event['StackId']
    responsebody['RequestId'] = event['RequestId']
    responsebody['LogicalResourceId'] = event['LogicalResourceId']
    responsebody['NoEcho'] = noEcho
    responsebody['Data'] = responseData

    json_responsebody = json.dumps(responsebody)

    print("Response body:\n" + json_responsebody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responsebody))
    }

    try:
        response = requests.put(responseurl,
                                data=json_responsebody,
                                headers=headers)
        print("Status code: " + response.reason)
    except Exception as exc:  # pylint: disable=broad-except
        print("send(..) failed executing requests.put(..): " + str(exc))
