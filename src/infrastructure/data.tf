# Prediction history is partitioned by user and ordered by creation time.
resource "aws_dynamodb_table" "prediction_history" {
  name         = "${local.name_prefix}-prediction-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "created_at_prediction_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "created_at_prediction_id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }
}

# Idempotency records prevent retries from creating duplicate saved predictions.
resource "aws_dynamodb_table" "prediction_idempotency" {
  name         = "${local.name_prefix}-prediction-idempotency"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "idempotency_key"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "idempotency_key"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled = true
  }
}
