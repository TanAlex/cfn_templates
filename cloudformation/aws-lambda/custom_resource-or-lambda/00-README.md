# Custom Resource

check event['RequestType']

Create, Update, Delete
```
if event['RequestType'] == 'Delete':
```

Get feeded variable 
```
StringLength=int(event['ResourceProperties']['StringLength'])
```

Send success result

Set the return variables in the responseData
```
responseData['RandomString'] = ''.join(random.choice(chars) for _ in range(StringLength))
cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
```

Send failed result

```
cfnresponse.send(event, context, cfnresponse.FAILED)
```


Usage:

ServiceToken -> the lambda function ARN
others will be the variables pass to the function

```  
  DbRootPassword:
    Type: Custom::DBRootPassword
    Properties:
      ServiceToken: !GetAtt RandomStrFunction.Arn
      StringLength: '8'
```


NOTE:
if you don't use cfnresponse.send function

you can use this, result is the same
```
def sendResponse(event, context, responseStatus, responseData):
    responseBody = json.dumps({
        "Status": responseStatus,
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": responseData
    })
    opener = build_opener(HTTPHandler)
    request = Request(event['ResponseURL'], data=responseBody)
    request.add_header('Content-Type', '')
    request.add_header('Content-Length', len(responseBody))
    request.get_method = lambda: 'PUT'
    response = opener.open(request)
    print("Status code: {}".format(response.getcode()))
    print("Status message: {}".format(response.msg))
    return responseBody
```