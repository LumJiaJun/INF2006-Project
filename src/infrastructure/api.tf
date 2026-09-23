data "archive_file" "health_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/health"
  output_path = "${path.module}/health.zip"
}

data "aws_iam_policy_document" "health_lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "health_lambda" {
  name               = "${local.name_prefix}-health-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.health_lambda_assume_role.json
}

data "aws_iam_policy_document" "health_lambda_logs" {
  statement {
    sid = "WriteHealthFunctionLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.health_lambda.arn}:*"]
  }
}

resource "aws_iam_role_policy" "health_lambda_logs" {
  name   = "write-health-function-logs"
  role   = aws_iam_role.health_lambda.id
  policy = data.aws_iam_policy_document.health_lambda_logs.json
}

resource "aws_cloudwatch_log_group" "health_lambda" {
  name              = "/aws/lambda/${local.name_prefix}-health"
  retention_in_days = 14
}

resource "aws_lambda_function" "health" {
  function_name = "${local.name_prefix}-health"
  description   = "Returns the public health status for the platform API"
  role          = aws_iam_role.health_lambda.arn
  runtime       = "python3.13"
  handler       = "handler.lambda_handler"
  architectures = ["arm64"]
  memory_size   = 128
  timeout       = 5

  filename         = data.archive_file.health_lambda.output_path
  source_code_hash = data.archive_file.health_lambda.output_base64sha256

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  depends_on = [
    aws_cloudwatch_log_group.health_lambda,
    aws_iam_role_policy.health_lambda_logs,
  ]
}

resource "aws_apigatewayv2_api" "platform" {
  name          = "${local.name_prefix}-api"
  protocol_type = "HTTP"
  description   = "Public API for the Airbnb Market Intelligence Platform"

  cors_configuration {
    allow_headers = ["content-type"]
    allow_methods = ["GET", "OPTIONS"]
    allow_origins = ["https://${aws_cloudfront_distribution.frontend.domain_name}"]
    max_age       = 300
  }
}

resource "aws_apigatewayv2_integration" "health" {
  api_id                 = aws_apigatewayv2_api.platform.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.health.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 5000
}

resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.platform.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.health.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.platform.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    detailed_metrics_enabled = true
    throttling_burst_limit   = 20
    throttling_rate_limit    = 10
  }
}

resource "aws_lambda_permission" "api_gateway_health" {
  statement_id  = "AllowApiGatewayHealthRoute"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.health.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.platform.execution_arn}/*/GET/health"
}

resource "aws_s3_object" "runtime_config" {
  bucket = aws_s3_bucket.frontend.id
  key    = "config.js"
  content = format(
    "window.APP_CONFIG = Object.freeze({ apiBaseUrl: %s });",
    jsonencode(aws_apigatewayv2_api.platform.api_endpoint)
  )
  content_type  = "application/javascript; charset=utf-8"
  cache_control = "no-cache"
}
