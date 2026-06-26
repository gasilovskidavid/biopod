resource "aws_dynamodb_table" "biopod_telemetry_db" {
  name         = "biopod-telemetry-db"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pod_id"
  range_key    = "timestamp"

  attribute {
    name = "pod_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }
}