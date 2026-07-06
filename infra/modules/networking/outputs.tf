output "vpc_id" {
  value = aws_vpc.main.id
}

output "subnet_id" {
  value = aws_subnet.public.id
}

output "subnet_id_b" {
  value = aws_subnet.public_b.id
}
