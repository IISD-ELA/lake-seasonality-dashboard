resource "aws_ssm_parameter" "api_endpoint" {
  name        = "/iisd-ela/config/lake-seasonality/api_endpoint"
  description = "Lake seasonality HTTP API endpoint used by shared application hosting"
  type        = "String"
  value       = aws_apigatewayv2_api.seasonality.api_endpoint
}
