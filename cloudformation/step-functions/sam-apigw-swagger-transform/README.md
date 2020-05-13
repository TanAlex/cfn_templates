https://stackoverflow.com/questions/42914487/how-to-invoke-an-aws-step-function-using-api-gateway

use SAM to setup ApiGateway and use the Swagger file define APIs

```
  RestApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      Name: !Sub ${AWS::StackName}-api
      DefinitionBody:
        'Fn::Transform':
          Name: AWS::Include
          Parameters:
            # s3 location of the swagger file
            Location: !Ref SwaggerS3File
```

in swagger.yaml, define the states:action/StartExecution

To export from apigateway
```
aws apigateway get-export --rest-api-id a1b2c3d4e5 \
  --stage-name dev \
  --export-type swagger /path/to/filename.json
```
swagger.yaml
```
    post:
      x-amazon-apigateway-integration:
        credentials:
          Fn::GetAtt: [ ApiGatewayStepFunctionsRole, Arn ]
        uri:
          Fn::Sub: arn:aws:apigateway:${AWS::Region}:states:action/StartExecution
        httpMethod: POST
        type: aws
        responses:
          default:
            statusCode: 200
            responseParameters:
              method.response.header.Access-Control-Allow-Headers:
                Fn::Sub: ${CorsHeaders}
              method.response.header.Access-Control-Allow-Origin:
                Fn::Sub: ${CorsOrigin}
          ".*CREATION_FAILED.*":
            statusCode: 403
            responseParameters:
              method.response.header.Access-Control-Allow-Headers:
                Fn::Sub: ${CorsHeaders}
              method.response.header.Access-Control-Allow-Origin:
                Fn::Sub: ${CorsOrigin}
            responseTemplates:
              application/json: $input.path('$.errorMessage')
        requestTemplates:
          application/json:
            Fn::Sub: |-
              {
                "input": "$util.escapeJavaScript($input.json('$'))",
                "name": "$context.requestId",
                "stateMachineArn": "${Workflow}"
              }
```