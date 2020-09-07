#----------------------------------
# ECS
#----------------------------------

output "ecs_cluster_id" {
  value = concat(aws_ecs_cluster.this.*.id, [""])[0]
}

output "ecs_cluster_arn" {
  value = concat(aws_ecs_cluster.this.*.arn, [""])[0]
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = var.ecs_name
}

#----------------------------------
# Instance Profile
#----------------------------------
output "instance_profile_id" {
  value = aws_iam_instance_profile.this.id
}

#----------------------------------
# ELB
#----------------------------------
output "this_elb_id" {
  description = "The name of the ELB"
  value       = module.elb.this_elb_id
}

output "this_elb_arn" {
  description = "The ARN of the ELB"
  value       = module.elb.this_elb_arn
}

output "this_elb_name" {
  description = "The name of the ELB"
  value       = module.elb.this_elb_name
}

output "this_elb_dns_name" {
  description = "The DNS name of the ELB"
  value       = module.elb.this_elb_dns_name
}
