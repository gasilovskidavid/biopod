terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-west-3"
}

resource "aws_kinesis_stream" "biopod-telemetry" {
  name             = "biopod-telemetry"
  shard_count      = 1
  retention_period = 24

  tags = {
    Project = "biopod"
  }
}