https://aws.amazon.com/blogs/networking-and-content-delivery/aggregating-lambdaedge-logs/


the lambda@edge function use 
console.log to log 

the log goes to cw, cw has a filter defined in create-subscription-filter
that will filter the log and send to kinesis firehose log 

The firhose AWS::KinesisFirehose::DeliveryStream
destination is the S3

The filter is using FilterPattern
FilterPattern – Enter a filter pattern, enclosed in double quotes (“”), to match the log events for your function.  In this example, we enter the text “Request Processed In” to capture only the events logged from our Lambda@Edge function.  To learn more about CloudWatch filter patterns, see Filter and Pattern Syntax in the Amazon CloudWatch Logs User Guide.

https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html