resource "aws_iam_role" "analyst" {
  name = "medmarket-analyst-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        AWS = "arn:aws:iam::${var.account_id}:root"
      }
    }]
  })

  tags = {
    Name        = "medmarket-analyst-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "analyst_s3_readonly" {
  name = "analyst-s3-readonly"
  role = aws_iam_role.analyst.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Resource = [
        "arn:aws:s3:::medmarket-processed-${var.environment}-${var.account_id}",
        "arn:aws:s3:::medmarket-processed-${var.environment}-${var.account_id}/*"
      ]
    }]
  })
}

resource "aws_iam_role" "engineer" {
  name = "medmarket-engineer-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        AWS = "arn:aws:iam::${var.account_id}:root"
      }
    }]
  })

  tags = {
    Name        = "medmarket-engineer-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "engineer_admin" {
  role       = aws_iam_role.engineer.name
  policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}
