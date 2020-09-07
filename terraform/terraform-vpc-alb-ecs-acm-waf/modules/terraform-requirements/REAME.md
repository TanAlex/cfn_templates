## The terraform-requirements folder is to create Terraform backend S3 and DynamoDB table

use the following to create

```
terraform init
terraform -var-file=${your_tfvars_file} plan
terraform -var-file=${your_tfvars_file} apply
```

For example:

```
terraform init -var-file=shared-us-west-1.tfvars
terraform plan -var-file="shared-us-west-1.tfvars"
terraform apply -var-file="shared-us-west-1.tfvars"
```