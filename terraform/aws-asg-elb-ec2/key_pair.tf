resource "aws_key_pair" "my-ssh-key" {
  key_name   = "my-ssh-key"
  public_key = "${file("id_rsa.pub")}"
}
