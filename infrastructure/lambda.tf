data "archive_file" "biopod_consumer_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/biopod_consumer.py"
  output_path = "${path.module}/build/biopod-consumer.zip"
}

resource "aws_lambda_function" "biopod_consumer" {
  function_name    = "biopod-consumer"
  role             = aws_iam_role.biopod_consumer_role.arn
  handler          = "biopod_consumer.lambda_handler"
  runtime          = "python3.11"
  filename         = data.archive_file.biopod_consumer_zip.output_path
  source_code_hash = data.archive_file.biopod_consumer_zip.output_base64sha256

  timeout     = 3
  memory_size = 128

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.biopod_telemetry_db.name
    }
  }
}

resource "aws_lambda_event_source_mapping" "biopod_consumer_trigger" {
  event_source_arn  = aws_kinesis_stream.biopod_telemetry.arn
  function_name     = aws_lambda_function.biopod_consumer.arn
  starting_position = "LATEST"
  batch_size        = 100
}