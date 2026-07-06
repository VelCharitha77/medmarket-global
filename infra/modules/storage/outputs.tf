output "raw_landing_bucket" {
  value = aws_s3_bucket.raw_landing.id
}

output "processed_bucket" {
  value = aws_s3_bucket.processed.id
}
