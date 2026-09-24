# A separate Lambda isolates optional AI traffic from core prediction scaling.
data "archive_file" "chat_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/chat"
  output_path = "${path.module}/chat.zip"
}

data "aws_iam_policy_document" "chat_lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "chat_lambda" {
  name               = "${local.name_prefix}-chat-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.chat_lambda_assume_role.json
}

resource "aws_cloudwatch_log_group" "chat_lambda" {
  name              = "/aws/lambda/${local.name_prefix}-chat"
  retention_in_days = 14
}

data "aws_iam_policy_document" "chat_lambda_access" {
  statement {
    sid     = "InvokeHaikuChatModel"
    actions = ["bedrock:InvokeModel"]
    resources = [
      "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/global.anthropic.claude-haiku-4-5-20251001-v1:0",
      "arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0",
    ]
  }

  statement {
    sid = "WriteChatFunctionLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.chat_lambda.arn}:*"]
  }
}

resource "aws_iam_role_policy" "chat_lambda_access" {
  name   = "invoke-haiku-and-write-logs"
  role   = aws_iam_role.chat_lambda.id
  policy = data.aws_iam_policy_document.chat_lambda_access.json
}

resource "aws_lambda_function" "chat" {
  function_name = "${local.name_prefix}-chat"
  description   = "Answers authenticated platform questions with Claude Haiku"
  role          = aws_iam_role.chat_lambda.arn
  runtime       = "python3.13"
  handler       = "handler.lambda_handler"
  architectures = ["arm64"]
  memory_size   = 256
  timeout       = 20

  filename         = data.archive_file.chat_lambda.output_path
  source_code_hash = data.archive_file.chat_lambda.output_base64sha256

  environment {
    variables = {
      BEDROCK_MODEL_ID = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  depends_on = [
    aws_cloudwatch_log_group.chat_lambda,
    aws_iam_role_policy.chat_lambda_access,
  ]
}

resource "aws_apigatewayv2_integration" "chat" {
  api_id                 = aws_apigatewayv2_api.platform.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.chat.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 20000
}

# Cognito prevents anonymous callers from spending Bedrock tokens.
resource "aws_apigatewayv2_route" "chat" {
  api_id             = aws_apigatewayv2_api.platform.id
  route_key          = "POST /chat"
  target             = "integrations/${aws_apigatewayv2_integration.chat.id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.users.id
}

resource "aws_lambda_permission" "api_gateway_chat" {
  statement_id  = "AllowApiGatewayChatRoute"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chat.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.platform.execution_arn}/*/POST/chat"
}
