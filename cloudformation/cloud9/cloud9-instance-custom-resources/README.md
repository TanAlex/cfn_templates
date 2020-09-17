https://observability.workshop.aws/en/installation/not_using_ee/_setup_cloud9.html

```
curl -O https://raw.githubusercontent.com/aws-samples/one-observability-demo/main/cloud9-cfn.yaml

aws cloudformation create-stack --stack-name C9-Observability-Workshop --template-body file://cloud9-cfn.yaml --capabilities CAPABILITY_NAMED_IAM
```

This script install AWS CLI, Kubectl, aws-iam-authenticator, eksctl, aws-cdk etc
```
curl -sSL https://raw.githubusercontent.com/aws-samples/one-observability-demo/main/PetAdoptions/envsetup.sh | bash -s stable

```

Setup local environment
```
export ACCOUNT_ID=$(aws sts get-caller-identity --output text --query Account)
export AWS_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r '.region')
echo "export ACCOUNT_ID=${ACCOUNT_ID}" | tee -a ~/.bash_profile
echo "export AWS_REGION=${AWS_REGION}" | tee -a ~/.bash_profile
aws configure set default.region ${AWS_REGION}
aws configure get default.region
```