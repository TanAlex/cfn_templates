resource "null_resource" "ansible-provision" {
  depends_on = ["aws_instance.aws-instance-01", "aws_instance.aws-instance-02"]

  provisioner "local-exec" {
    command = <<EOT
    cat > swarm-inventory <<EOL
[swarm-master]
${format("%s ansible_ssh_user=%s", aws_instance.aws-instance-01.0.public_ip, var.ansible_ssh_user)}

[swarm-nodes]
${format("%s ansible_ssh_user=%s", aws_instance.aws-instance-02.0.public_ip, var.ansible_ssh_user)}
EOL
EOT
  }

#command = "echo \"${join("\n",formatlist("%s ansible_ssh_user=%s", aws_instance.aws-swarm-members.*.public_ip, var.ansible_ssh_user))}\" >> swarm-inventory"


}