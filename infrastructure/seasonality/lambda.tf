resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = 14
}

resource "aws_lambda_function" "seasonality" {
  function_name = local.lambda_function_name
  role          = aws_iam_role.lambda.arn

  s3_bucket         = aws_s3_object.lambda.bucket
  s3_key            = aws_s3_object.lambda.key
  s3_object_version = aws_s3_object.lambda.version_id
  source_code_hash  = filebase64sha256(local.lambda_zip_path)
  handler           = "seasonality_app.handler.handler"
  runtime           = "python3.14"
  architectures     = ["x86_64"]

  timeout     = 29
  memory_size = 1024

  environment {
    variables = {
      ELA_API_BASE_URL        = local.ela_api_base_url
      ELA_API_MAX_ATTEMPTS    = "2"
      ELA_API_TIMEOUT_SECONDS = "8"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy_attachment.lambda_basic_execution,
  ]
}
