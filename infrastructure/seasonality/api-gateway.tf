resource "aws_apigatewayv2_api" "seasonality" {
  name          = "${local.name}-http-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "seasonality" {
  api_id                 = aws_apigatewayv2_api.seasonality.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.seasonality.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000
}

resource "aws_apigatewayv2_route" "ice_history" {
  api_id    = aws_apigatewayv2_api.seasonality.id
  route_key = "GET /api/ice-history"
  target    = "integrations/${aws_apigatewayv2_integration.seasonality.id}"
}

resource "aws_apigatewayv2_route" "ice_off" {
  api_id    = aws_apigatewayv2_api.seasonality.id
  route_key = "GET /api/ice-off"
  target    = "integrations/${aws_apigatewayv2_integration.seasonality.id}"
}

resource "aws_apigatewayv2_route" "lake_turnover" {
  api_id    = aws_apigatewayv2_api.seasonality.id
  route_key = "GET /api/lake-turnover"
  target    = "integrations/${aws_apigatewayv2_integration.seasonality.id}"
}

resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.seasonality.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.seasonality.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.seasonality.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.seasonality.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.seasonality.execution_arn}/*/*"
}
