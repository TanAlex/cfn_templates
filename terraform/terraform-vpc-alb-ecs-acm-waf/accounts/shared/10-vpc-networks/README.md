## switch to us-east-1 region and workspace
```
export WORKSPACE=shared-us-east-1
terraform init -var-file=${WORKSPACE}.tfvars -reconfigure -backend-config=backend-${WORKSPACE}.tfvars
terraform plan -var-file=${WORKSPACE}.tfvars -var-file=backend-${WORKSPACE}.tfvars -var="workspace=${WORKSPACE}"
terraform apply -var-file=${WORKSPACE}.tfvars -var-file=backend-${WORKSPACE}.tfvars -var="workspace=${WORKSPACE}"

```