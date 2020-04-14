#!/bin/bash
mkdir tempcloudwatch
cd tempcloudwatch
yum install wget -y
yum install unzip -y
wget https://s3.amazonaws.com/amazoncloudwatch-agent/linux/amd64/latest/AmazonCloudWatchAgent.zip
unzip AmazonCloudWatchAgent.zip
sudo ./install.sh
wget https://YOUR-PUBLIC-URL-HERE-WITH-CONFIG-FILE -O config.json
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:config.json -s