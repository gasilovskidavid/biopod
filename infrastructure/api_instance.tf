resource "aws_security_group" "api_server" {
  name        = "api-server-sg"
  description = "Security group for FastAPI read layer"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH from admin"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description     = "FastAPI from the Grafana instance only"
    protocol        = "tcp"
    from_port       = 8000
    to_port         = 8000
    security_groups = [aws_security_group.grafana_server.id]
  }

  egress {
    description = "Allow all outbound (pip install + DynamoDB API calls)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "api_server" {
  ami           = data.aws_ami.al2023_arm64.id
  instance_type = "t4g.micro" # arm64, to match the AMI architecture

  key_name               = aws_key_pair.admin.key_name
  iam_instance_profile   = aws_iam_instance_profile.api_server.name
  vpc_security_group_ids = [aws_security_group.api_server.id]
  subnet_id              = data.aws_subnets.default.ids[0]


  user_data_replace_on_change = true

  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    dnf install -y python3.11 python3.11-pip

    mkdir -p /opt/api

    cat > /opt/api/main.py <<'PY'
    ${file("${path.module}/../api/main.py")}
    PY

    cat > /opt/api/requirements.txt <<'REQ'
    ${file("${path.module}/../api/requirements.txt")}
    REQ

    # A venv keeps the uvicorn path deterministic instead of depending on
    # where a root-level `pip3 install` happens to drop console scripts.
    # Built with python3.11 explicitly, not bare `python3`: the latter is the
    # AMI's default interpreter, which is not guaranteed to be the 3.11 that
    # Lambda and CI run on.
    python3.11 -m venv /opt/api/venv
    /opt/api/venv/bin/pip install --upgrade pip
    /opt/api/venv/bin/pip install -r /opt/api/requirements.txt

    # Same configuration contract as api/main.py's load_dotenv(), sourced from Terraform.
    cat > /opt/api/.env <<'ENV'
    AWS_REGION=${var.aws_region}
    DYNAMODB_TABLE_NAME=${aws_dynamodb_table.biopod_telemetry_db.name}
    ENV

    chown -R ec2-user:ec2-user /opt/api
    chmod 600 /opt/api/.env

    cat > /etc/systemd/system/biopod-api.service <<'UNIT'
    [Unit]
    Description=Biopod FastAPI read layer
    After=network-online.target
    Wants=network-online.target

    [Service]
    User=ec2-user
    Group=ec2-user
    WorkingDirectory=/opt/api
    ExecStart=/opt/api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
    Restart=always

    [Install]
    WantedBy=multi-user.target
    UNIT

    systemctl daemon-reload
    systemctl enable --now biopod-api.service
  EOF

  tags = {
    Name = "biopod-api-server"
  }
}
