data "archive_file" "history_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/history"
  output_path = "${path.module}/history.zip"
}

data "aws_iam_policy_document" "history_lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "history_lambda" {
  name               = "${local.name_prefix}-history-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.history_lambda_assume_role.json
}

resource "aws_cloudwatch_log_group" "history_lambda" {
  name              = "/aws/lambda/${local.name_prefix}-history"
  retention_in_days = 14
}

data "aws_iam_policy_document" "history_lambda_access" {
  statement {
    sid       = "ReadOwnPredictionHistory"
    actions   = ["dynamodb:Query"]
    resources = [aws_dynamodb_table.prediction_history.arn]
  }

  statement {
    sid = "WriteHistoryFunctionLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.history_lambda.arn}:*"]
  }
}

resource "aws_iam_role_policy" "history_lambda_access" {
  name   = "read-history-and-write-logs"
  role   = aws_iam_role.history_lambda.id
  policy = data.aws_iam_policy_document.history_lambda_access.json
}

resource "aws_lambda_function" "history" {
  function_name = "${local.name_prefix}-history"
  description   = "Returns prediction history for the authenticated user"
  role          = aws_iam_role.history_lambda.arn
  runtime       = "python3.13"
  handler       = "handler.lambda_handler"
  architectures = ["arm64"]
  memory_size   = 128
  timeout       = 5

  filename         = data.archive_file.history_lambda.output_path
  source_code_hash = data.archive_file.history_lambda.output_base64sha256

  environment {
    variables = {
      HISTORY_TABLE_NAME = aws_dynamodb_table.prediction_history.name
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  depends_on = [
    aws_cloudwatch_log_group.history_lambda,
    aws_iam_role_policy.history_lambda_access,
  ]
}

resource "aws_apigatewayv2_integration" "history" {
  api_id                 = aws_apigatewayv2_api.platform.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.history.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 5000
}

resource "aws_apigatewayv2_route" "history" {
  api_id             = aws_apigatewayv2_api.platform.id
  route_key          = "GET /history"
  target             = "integrations/${aws_apigatewayv2_integration.history.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.users.id
}

resource "aws_lambda_permission" "api_gateway_history" {
  statement_id  = "AllowApiGatewayHistoryRoute"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.history.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.platform.execution_arn}/*/GET/history"
}

resource "aws_apigatewayv2_route" "authenticated_prediction" {
  api_id             = aws_apigatewayv2_api.platform.id
  route_key          = "POST /predictions"
  target             = "integrations/${aws_apigatewayv2_integration.prediction.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.users.id
}

resource "aws_lambda_permission" "api_gateway_authenticated_prediction" {
  statement_id  = "AllowApiGatewayAuthenticatedPredictionRoute"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.prediction.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.platform.execution_arn}/*/POST/predictions"
}
