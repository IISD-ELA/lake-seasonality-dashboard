resource "aws_cloudwatch_log_metric_filter" "upstream_failure" {
  name           = "${local.name}-upstream-failure"
  pattern        = "\"UPSTREAM_FAILURE\""
  log_group_name = aws_cloudwatch_log_group.lambda.name

  metric_transformation {
    name          = "UpstreamFailures"
    namespace     = "IISD/ELASeasonality"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_metric_alarm" "upstream_failure" {
  alarm_name          = "${local.name}-upstream-failure"
  alarm_description   = "The seasonality dashboard could not retrieve one or more upstream datasets."
  namespace           = "IISD/ELASeasonality"
  metric_name         = "UpstreamFailures"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 2
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = var.alarm_sns_topic_arn == null ? [] : [var.alarm_sns_topic_arn]
  ok_actions    = var.alarm_sns_topic_arn == null ? [] : [var.alarm_sns_topic_arn]
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.name}-lambda-errors"
  alarm_description   = "The seasonality Lambda returned an unhandled runtime error."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.seasonality.function_name
  }

  alarm_actions = var.alarm_sns_topic_arn == null ? [] : [var.alarm_sns_topic_arn]
  ok_actions    = var.alarm_sns_topic_arn == null ? [] : [var.alarm_sns_topic_arn]
}

resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "${local.name}-api-5xx"
  alarm_description   = "The seasonality HTTP API returned a server error."
  namespace           = "AWS/ApiGateway"
  metric_name         = "5xx"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = aws_apigatewayv2_api.seasonality.id
    Stage = aws_apigatewayv2_stage.default.name
  }

  alarm_actions = var.alarm_sns_topic_arn == null ? [] : [var.alarm_sns_topic_arn]
  ok_actions    = var.alarm_sns_topic_arn == null ? [] : [var.alarm_sns_topic_arn]
}
