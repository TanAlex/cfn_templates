## README ADVANCED

This is for the repo that uses Terraform Workspace feature

Terraform by default stores your state in the S3 bucket using the bucket-key specified in the `key` variable in `backend-${env}-${region}.tfvars` file. ( For example: vpc/terrafor.tfstate)

If you use Terraform Workspace, the bucket-key will be like
s3://${your-state-bucket_name}/env:/${workspace_name}/{$your_state_bucket_key}

Normally you don't need this feature. But if you need to deploy same repo to same account's same region, then Workspace might be helpful

If you do use Terraform Workspace, following these steps instead

modify both tfvars file to proper value
modify remote_state.tf to refer to existing backend state

```
export WORKSPACE=shared-us-east-1
terraform workspace select ${WORKSPACE}
terraform workspace show
terraform init -var-file=${WORKSPACE}.tfvars -reconfigure -backend-config=backend-${WORKSPACE}.tfvars
terraform plan -var-file=${WORKSPACE}.tfvars -var-file=backend-${WORKSPACE}.tfvars -var="workspace=${WORKSPACE}"
terraform apply -var-file=${WORKSPACE}.tfvars -var-file=backend-${WORKSPACE}.tfvars -var="workspace=${WORKSPACE}"


```