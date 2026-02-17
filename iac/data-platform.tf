resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "aws_ecr_repository" "service" {
  name                 = "${local.name_prefix}-service"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_dynamodb_table" "claims" {
  name         = "${local.name_prefix}-claims"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "claim_id"

  attribute {
    name = "claim_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_dynamodb_table" "claim_notes" {
  name         = "${local.name_prefix}-claim-notes"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "claim_id"
  range_key    = "note_id"

  attribute {
    name = "claim_id"
    type = "S"
  }

  attribute {
    name = "note_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}

resource "aws_s3_bucket" "claim_notes" {
  bucket = "${local.name_prefix}-claim-notes-${random_string.suffix.result}"
}

resource "aws_s3_bucket_versioning" "claim_notes" {
  bucket = aws_s3_bucket.claim_notes.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "claim_notes" {
  bucket = aws_s3_bucket.claim_notes.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_cloudwatch_log_group" "application" {
  name              = "/${local.name_prefix}/application"
  retention_in_days = var.log_retention_days
}
