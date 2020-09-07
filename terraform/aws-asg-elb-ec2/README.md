# Terraform repo  to create AWS stacks

## The following AWS resources are included
* One SSH Key pair
* One auto-scaling-group to automatically increase/decrease server capability
* 2 auto-scaling-policies (one increase and one 
decrease) based on CloudWatch metrics for CPUUsage
* One launch-configuration associates with auto-scaling-group for the EC2 instances. It has a simple user-data script to print "Hello World $hostname" to /index.html 
* One ELB which is attached to the auto-scaling-group
* VPC for us-west-2 region and one public subnet and one private subnet  
(TODO: add subnets for all 4 AZ and allow auto-scaling-group to scale to all 4 AZ)


## Usage:

* Copy variables.tf.example to variables.tf and update with proper AWS Access Credentials
* Update id_rsa.pub for proper public key
* Run terraform init, plan and apply

## Optional note:
You can checkout v1.0 tag which is a simple template for just basic generic stack without all these auto-scaling features