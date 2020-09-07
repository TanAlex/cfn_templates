# Generate a secure private key
resource "tls_private_key" "default" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Generate AWS keypair
resource "aws_key_pair" "default" {
  depends_on = [tls_private_key.default]
  key_name   = var.keyname
  public_key = tls_private_key.default.public_key_openssh
}

# Store the public and private keys in SSM parameter store
resource "aws_ssm_parameter" "private" {
  name  = var.ssm_parameter_privatekey
  type  = var.ssm_parameter_type
  value = tls_private_key.default.private_key_pem
}

resource "aws_ssm_parameter" "public" {
  name  = var.ssm_parameter_publickey
  type  = var.ssm_parameter_type
  value = tls_private_key.default.public_key_openssh
}