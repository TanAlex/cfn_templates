#!/bin/bash


yum -y install squid
systemctl start squid
systemctl enable squid
systemctl status squid


exists=$(aws s3 ls s3://yvr-dr-squid-automation-config-bucket/squid.conf)
if [ -z "$exists" ]; then   
  echo "it does not exist"; 
else   
  aws s3 cp s3://yvr-dr-squid-automation-config-bucket/squid.conf /etc/squid
  systemctl reload squid
fi

exit 0
