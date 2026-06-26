data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "biopod_consumer_role" {
  name               = "biopod-consumer-role-wd3uv7xv"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "biopod_consumer_policy" {
  statement {
    sid    = "KinesisReadStreamMinPolicy"
    effect = "Allow"
    actions = [
      "kinesis:GetRecords",
      "kinesis:GetShardIterator",
      "kinesis:DescribeStream",
      "kinesis:DescribeStreamSummary",
      "kinesis:ListShards"
    ]

    resources = [aws_kinesis_stream.biopod_telemetry.arn]
  }

  statement {
    sid    = "LambdaLogging"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = ["arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/biopod-consumer:*"]
  }

  statement {
    sid    = "MinWriteToDDB"
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:Query"
    ]

    resources = [aws_dynamodb_table.biopod_telemetry_db.arn]
  }

  statement {
    sid    = "SNSAlerting"
    effect = "Allow"
    actions = [
      "sns:Publish"
    ]

    resources = [aws_sns_topic.co2_alerts.arn]
  }
}

resource "aws_iam_role_policy" "biopod_consumer_policy" {
  name   = "biopod-consumer-policy"
  role   = aws_iam_role.biopod_consumer_role.id
  policy = data.aws_iam_policy_document.biopod_consumer_policy.json
}
