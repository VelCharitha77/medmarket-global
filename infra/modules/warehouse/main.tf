resource "aws_db_subnet_group" "main" {
  name       = "medmarket-db-subnet-group-${var.environment}"
  subnet_ids = [var.subnet_id, var.subnet_id_b]

  tags = {
    Name = "medmarket-db-subnet-group-${var.environment}"
  }
}

resource "aws_security_group" "warehouse" {
  name        = "medmarket-warehouse-sg-${var.environment}"
  description = "Allow Postgres access"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "medmarket-warehouse-sg-${var.environment}"
  }
}

resource "aws_db_instance" "warehouse" {
  identifier             = "medmarket-warehouse-${var.environment}"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  db_name                = "medmarket"
  username               = "postgres"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.warehouse.id]
  publicly_accessible    = true
  skip_final_snapshot    = true

  tags = {
    Name        = "medmarket-warehouse-${var.environment}"
    Environment = var.environment
  }
}
