# https://github.com/tkant/elasticsearch-terraform-ecs

resource "aws_efs_file_system" "elk-efs-data" {
  creation_token = "es-persistent-data"
  performance_mode = "generalPurpose"
  # throughput_mode = "bursting"
  # encrypted = "true"
  tags = {
    Name = "elasticsearch-ecs-efs"
  }
}

resource "aws_efs_mount_target" "elasticsearch" {
  count = length(local.lookups.private_subnets)
  file_system_id = aws_efs_file_system.elk-efs-data.id
  #subnet_id      = "${element(split(",", var.private_subnet_ids), count.index )}"
  subnet_id = local.lookups.private_subnets[count.index]
  security_groups = [aws_security_group.elk-efs-securitygroup.id]
}

# User data template that specifies how to bootstrap each instance
data "template_file" "user-data-with-efs" {
  template = file("${path.module}/templates/user-data-with-efs.sh")

  vars = {
    ecs_name = var.ecs_name
    efs_file_system_id = aws_efs_file_system.elk-efs-data.id
  }
}

#----------------------------------
# Security Groups
#----------------------------------
resource "aws_security_group" "elk-efs-securitygroup" {
   name = "elk-efs-securitygroup"
   vpc_id = local.lookups.vpc_id
   description = "Security Group for EFS to allow NFS connection"
   // NFS
   ingress {
     self = true
     from_port = 2049
     to_port = 2049
     protocol = "tcp"
   }

   // Terraform removes the default rule
   egress {
     cidr_blocks = ["0.0.0.0/0"]
     from_port = 0
     to_port = 0
     protocol = "-1"
   }
 }