resource "aws_security_group" "grafana_server" {
  name        = "grafana-server-sg"
  description = "Security group for the Grafana dashboard host"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH from admin"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "Grafana web UI from admin"
    protocol    = "tcp"
    from_port   = 3000
    to_port     = 3000
    cidr_blocks = [var.my_ip]
  }

  egress {
    description = "Allow all outbound (package install + calls to the API instance)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
