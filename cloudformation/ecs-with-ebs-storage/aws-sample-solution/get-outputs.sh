#!/bin/bash
function usage {
  echo "usage: source <(./get-outputs.sh <stackname-or-stackid> <region>)"
  echo "stack name or ID must be provided or exported as the CloudFormationStack environment variable"
  echo "region must be provided or set with aws configure"
}

function main {
    #Get stack
    if [ -z "$1" ]; then
        if [ -z "$CloudFormationStack" ]; then
            echo "please provide stack name or ID"
            usage
            exit 1
        fi
    else
        CloudFormationStack="$1"
    fi
    #Get region
    if [ -z "$2" ]; then
        region=$(aws configure get region)
        if [ -z $region ]; then
            echo "please provide region"
            usage
            exit 1
        fi
    else
        region="$2"
    fi
    
    echo "#Region: $region"
    echo "#Stack: $CloudFormationStack"
    echo "#---"
    
    echo "#Checking if stack exists..."
    aws cloudformation wait stack-exists \
    --region $region \
    --stack-name $CloudFormationStack
    
    echo "#Checking if stack creation is complete..."
    aws cloudformation wait stack-create-complete \
    --region $region \
    --stack-name $CloudFormationStack
     
    echo "#Getting output keys and values..."
    echo "#---"
    aws cloudformation describe-stacks \
    --region $region \
    --stack-name $CloudFormationStack \
    --query 'Stacks[].Outputs[].[OutputKey, OutputValue]' \
    --output text | awk '{print "export", $1"="$2}'
}
main "$@"