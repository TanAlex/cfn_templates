# Automating bucketing of streaming data using Amazon Athena and AWS Lambda

https://aws.amazon.com/blogs/big-data/automating-bucketing-of-streaming-data-using-amazon-athena-and-aws-lambda/

The workflow in this project is like these:

### Deploy Kinese Data Generator Tool  

### Deploy CloudFormation stack to create a Kinesis Firehose Delivery Stream.The destination is S3 with an optional processing lambda (in our case, I disabled it, just want to stream directly to S3).

This Kinesis Stream has an important setting to partition the data in S3.NOTE: partition is set on the Prefix and ErrorOutpuPrefix lines
```
  DeliveryStream:
    Type: AWS::KinesisFirehose::DeliveryStream
    Properties:
      ExtendedS3DestinationConfiguration:
        BucketARN: !Sub 'arn:aws:s3:::${S3Bucket}'
        BufferingHints:
          IntervalInSeconds: 60
          SizeInMBs: 50
        CompressionFormat: UNCOMPRESSED
        Prefix: "raw/dt=!{timestamp:yyyy}-!{timestamp:MM}-!{timestamp:dd}-!{timestamp:HH}/"
        ErrorOutputPrefix: "FirehoseFailures/!{firehose:error-output-type}/"
        RoleARN: !GetAtt DeliveryRole.Arn
```

### Use Athena to create Database and a SourceTable
```
CREATE DATABASE mydatabase;

CREATE EXTERNAL TABLE mydatabase.SourceTable(
  sensorid string, 
  currenttemperature int, 
  status string)
PARTITIONED BY ( 
  dt string)
ROW FORMAT SERDE 
  'org.openx.data.jsonserde.JsonSerDe' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.IgnoreKeyTextOutputFormat'
LOCATION
  's3://lab-test-storage-demos/raw/';
```


For any new partition, you have to run 
`MSCK REPAIR TABLE SourceTable;`
again, otherwise it won't show up in Athena

### Create a TargetTable using CTAS (Creating a Table from Query Results )

```
CREATE TABLE TargetTable
WITH (
      format = 'PARQUET', 
      external_location = 's3://<s3_bucket_name>/curated/', 
      partitioned_by = ARRAY['dt'], 
      bucketed_by = ARRAY['sensorID'], 
      bucket_count = 3) 
AS SELECT *
FROM SourceTable
```