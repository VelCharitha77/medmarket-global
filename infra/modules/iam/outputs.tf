output "analyst_role_arn" {
  value = aws_iam_role.analyst.arn
}

output "engineer_role_arn" {
  value = aws_iam_role.engineer.arn
}
