resource "null_resource" "rerun" {
    triggers {
      rerun = "${uuid()}"
    }
    connection {
        type = "ssh"
        user = "ubuntu"
        private_key   = "${file("~/.ssh/id_rsa")}"
        host = "${aws_instance.aws-instance-01.public_ip}"
    }

    provisioner "remote-exec" {
      inline = [
        "sudo apt-get update",
        "sudo apt-get -y install ansible",
      ]
    }
}