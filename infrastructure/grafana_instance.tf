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

resource "aws_instance" "grafana_server" {
  ami           = data.aws_ami.al2023_arm64.id
  instance_type = "t4g.micro"

  key_name               = aws_key_pair.admin.key_name
  vpc_security_group_ids = [aws_security_group.grafana_server.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  user_data_replace_on_change = true

  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    dnf install -y https://dl.grafana.com/oss/release/grafana-11.6.0-1.aarch64.rpm

    systemctl enable --now grafana-server

    grafana-cli plugins install yesoreyeram-infinity-datasource

    chown -R grafana:grafana /var/lib/grafana/plugins
    chmod -R 755 /var/lib/grafana/plugins

    systemctl restart grafana-server
  EOF

  tags = {
    Name = "biopod-grafana-server"
  }
}
