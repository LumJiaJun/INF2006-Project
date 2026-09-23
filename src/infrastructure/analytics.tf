# This Lambda queries the governed Athena workgroup for approved city summaries.
data "archive_file" "analytics_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/analytics"
  output_path = "${path.module}/analytics.zip"
}

data "aws_iam_policy_document" "analytics_lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "analytics_lambda" {
  name               = "${local.name_prefix}-analytics-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.analytics_lambda_assume_role.json
}

resource "aws_cloudwatch_log_group" "analytics_lambda" {
  name              = "/aws/lambda/${local.name_prefix}-analytics"
  retention_in_days = 14
}

data "aws_iam_policy_document" "analytics_lambda_access" {
  statement {
    sid = "RunGovernedAthenaQueries"
    actions = [
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:StartQueryExecution",
      "athena:StopQueryExecution",
    ]
    resources = [aws_athena_workgroup.analytics.arn]
  }

  statement {
    sid = "ReadAnalyticsCatalog"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetPartition",
      "glue:GetPartitions",
      "glue:GetTable",
      "glue:GetTables",
    ]
    resources = [
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:catalog",
      aws_glue_catalog_database.analytics.arn,
      aws_glue_catalog_table.listings.arn,
    ]
  }

  statement {
    sid = "ListAnalyticsData"
    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucket",
    ]
    resources = [aws_s3_bucket.data_lake.arn]
  }

  statement {
    sid = "ReadProcessedAndWriteResults"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.data_lake.arn}/processed/listings/*",
      "${aws_s3_bucket.data_lake.arn}/analytics/query-results/*",
    ]
  }

  statement {
    sid = "WriteAnalyticsFunctionLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.analytics_lambda.arn}:*"]
  }
}

resource "aws_iam_role_policy" "analytics_lambda_access" {
  name   = "query-analytics-and-write-logs"
  role   = aws_iam_role.analytics_lambda.id
  policy = data.aws_iam_policy_document.analytics_lambda_access.json
}

resource "aws_lambda_function" "analytics" {
  function_name = "${local.name_prefix}-analytics"
  description   = "Returns approved Airbnb city analytics from Athena"
  role          = aws_iam_role.analytics_lambda.arn
  runtime       = "python3.13"
  handler       = "handler.lambda_handler"
  architectures = ["arm64"]
  memory_size   = 256
  timeout       = 15

  filename         = data.archive_file.analytics_lambda.output_path
  source_code_hash = data.archive_file.analytics_lambda.output_base64sha256

  environment {
    variables = {
      ATHENA_DATABASE_NAME  = aws_glue_catalog_database.analytics.name
      ATHENA_TABLE_NAME     = aws_glue_catalog_table.listings.name
      ATHENA_WORKGROUP_NAME = aws_athena_workgroup.analytics.name
    }
  }

  logging_config {
    log_format            = "JSON"
    application_log_level = "INFO"
    system_log_level      = "WARN"
  }

  depends_on = [
    aws_cloudwatch_log_group.analytics_lambda,
    aws_iam_role_policy.analytics_lambda_access,
  ]
}

# API Gateway exposes the read-only analytics route to the frontend.
resource "aws_apigatewayv2_integration" "analytics" {
  api_id                 = aws_apigatewayv2_api.platform.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.analytics.invoke_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 15000
}

resource "aws_apigatewayv2_route" "analytics" {
  api_id    = aws_apigatewayv2_api.platform.id
  route_key = "GET /analytics"
  target    = "integrations/${aws_apigatewayv2_integration.analytics.id}"
}

resource "aws_lambda_permission" "api_gateway_analytics" {
  statement_id  = "AllowApiGatewayAnalyticsRoute"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.analytics.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.platform.execution_arn}/*/GET/analytics"
}
