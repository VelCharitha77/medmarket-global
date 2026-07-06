resource "aws_s3_bucket" "raw_landing" {
  bucket = "medmarket-raw-landing-${var.environment}-${var.account_suffix}"

  tags = {
    Name        = "medmarket-raw-landing-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "processed" {
  bucket = "medmarket-processed-${var.environment}-${var.account_suffix}"

  tags = {
    Name        = "medmarket-processed-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "raw_landing" {
  bucket = aws_s3_bucket.raw_landing.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "raw_landing" {
  bucket = aws_s3_bucket.raw_landing.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "processed" {
  bucket = aws_s3_bucket.processed.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
