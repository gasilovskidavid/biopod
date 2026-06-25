resource "aws_kinesis_stream" "biopod_telemetry" {
  name             = "biopod-telemetry"
  shard_count      = 1
  retention_period = 24

  tags = {
    Project = "biopod"
  }
}