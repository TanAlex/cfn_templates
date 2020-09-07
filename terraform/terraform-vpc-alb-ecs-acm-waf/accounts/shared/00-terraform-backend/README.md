## switch to us-east-1 region and workspace
```
export WORKSPACE=shared-us-east-1
terraform workspace new ${WORKSPACE}
terraform workspace select ${WORKSPACE}
terraform workspace show
terraform init -var-file=${WORKSPACE}.tfvars
terraform plan -var-file=${WORKSPACE}.tfvars
terraform apply -var-file=${WORKSPACE}.tfvars

```