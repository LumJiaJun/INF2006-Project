# The image tag selects the immutable model container deployed to Lambda.
variable "prediction_image_tag" {
  description = "Immutable ECR image tag used by the prediction Lambda."
  type        = string
  default     = "1.0.3"
}

data "aws_iam_policy_document" "prediction_lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "prediction_lambda" {
  name               = "${local.name_prefix}-prediction-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.prediction_lambda_assume_role.json
}

resource "aws_cloudwatch_log_group" "prediction_lambda" {
  name              = "/aws/lambda/${local.name_prefix}-prediction"
  retention_in_days = 14
}

data "aws_iam_policy_document" "prediction_lambda_logs" {
  statement {
    sid       = "WritePredictionHistory"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.prediction_history.arn]
  }

  statement {
    sid = "WritePredictionFunctionLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.prediction_lambda.arn}:*"]
  }
}

resource "aws_iam_role_policy" "prediction_lambda_logs" {
  name   = "prediction-history-and-logs"
  role   = aws_iam_role.prediction_lambda.id
  policy = data.aws_iam_policy_document.prediction_lambda_logs.json
}

# The prediction Lambda validates inputs, runs the model, and can save history.
resource "aws_lambda_function" "prediction" {
  function_name = "${local.name_prefix}-prediction"
  description   = "Validates listing details and returns an estimated nightly price"
  role          = aws_iam_role.prediction_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.prediction.repository_url}:${var.prediction_image_tag}"
  architectures = ["x86_64"]
  memory_size   = 2048
  timeout       = 20

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  environment {
    variables = {
      HISTORY_TABLE_NAME = aws_dynamodb_table.prediction_history.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.prediction_lambda,
    aws_iam_role_policy.prediction_lambda_logs,
  ]
}

resource "aws_apigatewayv2_integration" "prediction" {
  api_id                 = aws_apigatewayv2_api.platform.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.prediction.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 20000
}

# This public route supports estimates without requiring an account.
resource "aws_apigatewayv2_route" "prediction" {
  api_id    = aws_apigatewayv2_api.platform.id
  route_key = "POST /predict"
  target    = "integrations/${aws_apigatewayv2_integration.prediction.id}"
}

resource "aws_lambda_permission" "api_gateway_prediction" {
  statement_id  = "AllowApiGatewayPredictionRoute"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.prediction.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.platform.execution_arn}/*/POST/predict"
}

resource "aws_s3_object" "model_options" {
  bucket        = aws_s3_bucket.frontend.id
  key           = "model-options.json"
  source        = "${path.module}/../frontend/model-options.json"
  etag          = filemd5("${path.module}/../frontend/model-options.json")
  content_type  = "application/json; charset=utf-8"
  cache_control = "no-cache"
}
