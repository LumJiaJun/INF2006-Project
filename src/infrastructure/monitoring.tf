data "aws_iam_policy_document" "operational_alerts_key" {
  statement {
    sid       = "EnableAccountKeyAdministration"
    actions   = ["kms:*"]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }

  statement {
    sid = "AllowCloudWatchAlarmPublishing"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*",
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:cloudwatch:${var.aws_region}:${data.aws_caller_identity.current.account_id}:alarm:${local.name_prefix}-*"]
    }
  }
}

resource "aws_kms_key" "operational_alerts" {
  description             = "Encrypts the operational alarm SNS topic"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.operational_alerts_key.json
}

resource "aws_kms_alias" "operational_alerts" {
  name          = "alias/${local.name_prefix}-operational-alerts"
  target_key_id = aws_kms_key.operational_alerts.key_id
}

resource "aws_sns_topic" "operational_alerts" {
  name              = "${local.name_prefix}-operational-alerts"
  kms_master_key_id = aws_kms_key.operational_alerts.arn
}

resource "aws_cloudwatch_metric_alarm" "api_server_errors" {
  alarm_name          = "${local.name_prefix}-api-server-errors"
  alarm_description   = "API Gateway returned one or more server errors in five minutes"
  namespace           = "AWS/ApiGateway"
  metric_name         = "5xx"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.operational_alerts.arn]
  ok_actions          = [aws_sns_topic.operational_alerts.arn]

  dimensions = {
    ApiId = aws_apigatewayv2_api.platform.id
    Stage = aws_apigatewayv2_stage.default.name
  }
}

resource "aws_cloudwatch_metric_alarm" "prediction_errors" {
  alarm_name          = "${local.name_prefix}-prediction-errors"
  alarm_description   = "Prediction Lambda returned one or more unhandled errors in five minutes"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.operational_alerts.arn]
  ok_actions          = [aws_sns_topic.operational_alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.prediction.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "analytics_errors" {
  alarm_name          = "${local.name_prefix}-analytics-errors"
  alarm_description   = "Analytics Lambda returned one or more unhandled errors in five minutes"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.operational_alerts.arn]
  ok_actions          = [aws_sns_topic.operational_alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.analytics.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "health_throttles" {
  alarm_name          = "${local.name_prefix}-health-throttles"
  alarm_description   = "Health Lambda was throttled one or more times in five minutes"
  namespace           = "AWS/Lambda"
  metric_name         = "Throttles"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  datapoints_to_alarm = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.operational_alerts.arn]
  ok_actions          = [aws_sns_topic.operational_alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.health.function_name
  }
}

resource "aws_cloudwatch_dashboard" "operations" {
  dashboard_name = "${local.name_prefix}-operations"
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          title  = "API requests and errors"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiId", aws_apigatewayv2_api.platform.id, "Stage", aws_apigatewayv2_stage.default.name],
            [".", "4xx", ".", ".", ".", "."],
            [".", "5xx", ".", ".", ".", "."],
            [".", "IntegrationLatency", ".", ".", ".", ".", { stat = "p95", yAxis = "right" }],
          ]
        }
      },
      {
        type   = "metric"
        width  = 12
        height = 6
        properties = {
          title  = "Lambda duration and errors"
          region = var.aws_region
          period = 300
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.prediction.function_name, { stat = "p95" }],
            [".", "Errors", ".", ".", { stat = "Sum", yAxis = "right" }],
            [".", "Invocations", ".", ".", { stat = "Sum", yAxis = "right" }],
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.analytics.function_name, { stat = "p95" }],
            [".", "Errors", ".", ".", { stat = "Sum", yAxis = "right" }],
            ["AWS/Lambda", "Throttles", "FunctionName", aws_lambda_function.health.function_name, { stat = "Sum", yAxis = "right" }],
          ]
        }
      },
    ]
  })
}
