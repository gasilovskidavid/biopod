data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc_id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "api_server" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "architecture"
    values = ["arm64"]
  }
  filter {
    name   = "name"
    values = ["al2023-ami-2023*"]
  }
}

# ---------------------------------------------------------------------------
# IAM: let the instance Query the telemetry table (matches api/main.py usage)
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "api_server_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "api_server" {
  name               = "biopod-api-server-role"
  assume_role_policy = data.aws_iam_policy_document.api_server_assume_role.json
}

data "aws_iam_policy_document" "api_server" {
  statement {
    sid    = "ReadTelemetryTable"
    effect = "Allow"
    actions = [
      "dynamodb:Query",
      "dynamodb:DescribeTable"
    ]

    resources = [aws_dynamodb_table.biopod_telemetry_db.arn]
  }
}

resource "aws_iam_role_policy" "api_server" {
  name   = "biopod-api-server-policy"
  role   = aws_iam_role.api_server.id
  policy = data.aws_iam_policy_document.api_server.json
}

resource "aws_iam_instance_profile" "api_server" {
  name = "biopod-api-server-profile"
  role = aws_iam_role.api_server.name
}

# ---------------------------------------------------------------------------
# Security group for the FastAPI read layer
# ---------------------------------------------------------------------------
resource "aws_security_group" "api_server" {
  name        = "api-server-sg"
  description = "Security group for FastAPI read layer"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "FastAPI read layer"
    protocol    = "tcp"
    # TODO_CONFIGURE: API port (must match the --port in the systemd unit below; uvicorn default is 8000)
    # from_port = 8000
    # to_port   = 8000
    # TODO_CONFIGURE: who may reach the API, e.g. ["0.0.0.0/0"] for public or your office CIDR
    # cidr_blocks = ["x.x.x.x/32"]
  }

  egress {
    description = "Allow all outbound (pip install + DynamoDB API calls)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------------------------------------------------------------------------
# EC2 instance that boots already running api/main.py via uvicorn
# ---------------------------------------------------------------------------
resource "aws_instance" "api_server" {
  ami           = data.aws_ami.api_server.id
  instance_type = "t3.micro"

  # TODO_CONFIGURE: optional SSH key pair name for shell access (SSM works without one)
  # key_name = "my-key-pair"

  iam_instance_profile   = aws_iam_instance_profile.api_server.name
  vpc_security_group_ids = [aws_security_group.api_server.id]
  subnet_id              = data.aws_subnets.default.ids[0]

  instance_market_options {
    market_type = "spot"
    spot_options {
      # max price left unset for now, set after test
    }
  }

  # Bootstrap: install Python, drop in api/main.py (single source of truth via file()),
  # install pinned deps, write the same env vars as api/.env, and run uvicorn under systemd.
  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    dnf install -y python3 python3-pip

    mkdir -p /opt/api

    cat > /opt/api/main.py <<'PY'
    ${file("${path.module}/../api/main.py")}
    PY

    cat > /opt/api/requirements.txt <<'REQ'
    ${file("${path.module}/../api/requirements.txt")}
    REQ

    pip3 install -r /opt/api/requirements.txt

    # Same configuration contract as api/main.py's load_dotenv(), sourced from Terraform.
    cat > /opt/api/.env <<'ENV'
    AWS_REGION=${var.aws_region}
    DYNAMODB_TABLE_NAME=${aws_dynamodb_table.biopod_telemetry_db.name}
    ENV

    cat > /etc/systemd/system/biopod-api.service <<'UNIT'
    [Unit]
    Description=Biopod FastAPI read layer
    After=network-online.target
    Wants=network-online.target

    [Service]
    WorkingDirectory=/opt/api
    # TODO_CONFIGURE: --port must match the security group ingress port above (uvicorn default is 8000)
    ExecStart=/usr/local/bin/uvicorn main:app --host 0.0.0.0 --port 8000
    Restart=always

    [Install]
    WantedBy=multi-user.target
    UNIT

    systemctl daemon-reload
    systemctl enable --now biopod-api.service
  EOF
}
