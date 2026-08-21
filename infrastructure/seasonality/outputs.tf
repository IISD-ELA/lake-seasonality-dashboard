output "site_url" {
  value = "https://${aws_cloudfront_distribution.seasonality.domain_name}"
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.seasonality.api_endpoint
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.seasonality.id
}

output "lambda_function_name" {
  value = aws_lambda_function.seasonality.function_name
}

output "static_bucket_name" {
  value = aws_s3_bucket.static.id
}

output "artifact_bucket_name" {
  value = aws_s3_bucket.artifacts.id
}

output "upstream_failure_alarm_name" {
  value = aws_cloudwatch_metric_alarm.upstream_failure.alarm_name
}

output "lambda_error_alarm_name" {
  value = aws_cloudwatch_metric_alarm.lambda_errors.alarm_name
}

output "api_5xx_alarm_name" {
  value = aws_cloudwatch_metric_alarm.api_5xx.alarm_name
}
