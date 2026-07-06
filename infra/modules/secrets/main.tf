resource "aws_secretsmanager_secret" "hubspot_api_key" {
  name = "medmarket-hubspot-api-key-${var.environment}"

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret" "five9_credentials" {
  name = "medmarket-five9-credentials-${var.environment}"

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret" "modio_api_key" {
  name = "medmarket-modio-api-key-${var.environment}"

  tags = {
    Environment = var.environment
  }
}
