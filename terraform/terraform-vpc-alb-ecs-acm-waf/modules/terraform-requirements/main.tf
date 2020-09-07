// Terraform code to boostrap AWS environment with the following resources
// - s3 bucket for terraform state
// - dynamodb table to store locking information to prevent multiple Terraform clients from
//   mutating the AWS environment at the same time

// S3 bucket for Terraform state
resource "aws_s3_bucket" "tf_state_bucket" {
  bucket = var.tf_state_bucket_name // S3 bucket name
  acl    = "private"                // Canned ACL set to private to allows owner to get full access and noone else
  tags   = var.tags                 // AWS resource tags
  region = var.region               // AWS region to store the bucket

  // S3 bucket versioning on objects such that recovery can be done unintended object changes
  versioning {
    enabled = true
  }
}

// Dynamodb table to store terraform lock information
resource "aws_dynamodb_table" "tf_state_lock" {
  // Dynamodb table attributes
  attribute {
    name = "LockID"
    type = "S"
  }

  read_capacity  = var.lock_table_read_capacity    // Dynamodb table read throughput
  write_capacity = var.lock_table_write_capacity   // Dynamodb table write throughput
  hash_key       = "LockID"                        // Table primary key
  name           = var.tf_dynamodb_lock_table_name // Dynamodb table name
  tags           = var.tags                        // Resource tag

  // Hook to override terraform default life cycle behaviour
  lifecycle {
    // Prevent destruction is an explicitly added step to ensure terraform plan that includes
    // deleting this resource will return an error
    prevent_destroy = true
  }
}


// Bucket policy for cross account access from Jenkins and Admin user
// TODO: will be uncommented and enabled once roles are created in the relevant accounts
//resource "aws_s3_bucket_policy" "bucket_policy" {
//  bucket = "${aws_s3_bucket.dev_state_bucket.id}"
//
//  policy = <<POLICY
//{
//    "Version": "2012-10-17",
//    "Statement": [
//        {
//            "Effect": "Allow",
//            "Principal": {
//                "AWS": "arn:aws:iam::748569899255:role/placeholder1"
//            },
//            "Action": [
//                "s3:GetObject",
//                "s3:PutObject"
//            ],
//            "Resource": [
//                "arn:aws:s3:::${var.tf_state_bucket_name}",
//                "arn:aws:s3:::${var.tf_state_bucket_name}/*"
//            ]
//        },
//        {
//            "Effect": "Allow",
//            "Principal": {
//                "AWS": "arn:aws:iam::748569899255:role/placeholder2"
//            },
//            "Action": [
//                "s3:GetObject"
//            ],
//            "Resource": [
//                "arn:aws:s3:::${var.tf_state_bucket_name}",
//                "arn:aws:s3:::${var.tf_state_bucket_name}/*"
//            ]
//        }
//    ]
//}
//POLICY
//}
