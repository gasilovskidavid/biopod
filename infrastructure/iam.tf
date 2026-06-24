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

resource "aws_iam_role" "biopod-consumer-role" {
  name               = "biopod-consumer-role-wd3uv7xv"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

data "aws_iam_policy_document" "biopod-consumer-policy" {
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

    resources = [aws_kinesis_stream.biopod-telemetry.arn]
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
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role_policy" "biopod-consumer-policy" {
  name   = "biopod-consumer-policy"
  role   = aws_iam_role.biopod-consumer-role.id
  policy = data.aws_iam_policy_document.biopod-consumer-policy.json
}

