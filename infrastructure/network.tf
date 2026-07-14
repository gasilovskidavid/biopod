data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "al2023_arm64" {
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

resource "aws_key_pair" "admin" {
  key_name   = "biopod-admin-key"
  public_key = var.ssh_public_key
}
