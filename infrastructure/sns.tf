resource "aws_sns_topic" "co2_alerts" {
  name = "biopod-co2-alerts"
}

resource "aws_sns_topic_subscription" "user_updates_sqs_target" {
  topic_arn = aws_sns_topic.co2_alerts.arn
  protocol  = "sqs"
  endpoint  = var.alert_mail
}