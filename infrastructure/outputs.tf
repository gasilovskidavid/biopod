output "api_server_public_ip" {
  description = "SSH here: ssh ec2-user@<this>"
  value       = aws_instance.api_server.public_ip
}

output "api_server_private_ip" {
  description = "Grafana reaches the API on the VPC-internal address, not the public one."
  value       = aws_instance.api_server.private_ip
}

output "api_datasource_url" {
  description = "Base URL to configure as the Grafana JSON/Infinity datasource."
  value       = "http://${aws_instance.api_server.private_ip}:8000"
}

output "grafana_server_public_ip" {
  description = "Browser here: http://<this>:3000"
  value       = aws_instance.grafana_server.public_ip
}
