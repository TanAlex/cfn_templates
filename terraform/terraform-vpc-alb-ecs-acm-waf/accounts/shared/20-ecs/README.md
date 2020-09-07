## switch to us-east-1 region and workspace

modify both tfvars file to proper value
modify remote_state.tf to refer to existing backend state

```
export WORKSPACE=shared-us-east-1
terraform init -var-file=${WORKSPACE}.tfvars -reconfigure -backend-config=backend-${WORKSPACE}.tfvars
terraform plan -var-file=${WORKSPACE}.tfvars -var-file=backend-${WORKSPACE}.tfvars 
terraform apply -var-file=${WORKSPACE}.tfvars -var-file=backend-${WORKSPACE}.tfvars 


```