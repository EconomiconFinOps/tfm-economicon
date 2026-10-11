resource "aws_sns_topic" "alarms" {
  name = "${local.name}-alarms"
  # No subscriptions or messages are created/sent by this reference.
}
resource "aws_cloudwatch_metric_alarm" "api_errors" {
  alarm_name          = "${local.name}-api-target-5xx"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"
  dimensions          = { LoadBalancer = aws_lb.api.arn_suffix }
  alarm_actions       = [aws_sns_topic.alarms.arn]
}
resource "aws_cloudwatch_metric_alarm" "db_storage" {
  for_each            = aws_db_instance.main
  alarm_name          = "${local.name}-${each.key}-storage"
  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  period              = 300
  statistic           = "Minimum"
  threshold           = 5368709120
  treat_missing_data  = "missing"
  dimensions          = { DBInstanceIdentifier = each.value.identifier }
  alarm_actions       = [aws_sns_topic.alarms.arn]
}
