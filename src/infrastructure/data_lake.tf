# The private data lake stores raw files, processed Parquet, and query results.
data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "data_lake" {
  bucket        = "${local.name_prefix}-data-${random_id.bucket_suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "expire-athena-results"
    status = "Enabled"

    filter {
      prefix = "analytics/query-results/"
    }

    expiration {
      days = 7
    }
  }

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# Terraform uploads the Glue script so the managed ETL job can run it.
resource "aws_s3_object" "glue_transform" {
  bucket        = aws_s3_bucket.data_lake.id
  key           = "scripts/glue_transform.py"
  source        = "${path.module}/../../analytics/glue_transform.py"
  etag          = filemd5("${path.module}/../../analytics/glue_transform.py")
  content_type  = "text/x-python; charset=utf-8"
  cache_control = "no-cache"
}

data "aws_iam_policy_document" "glue_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue_transform" {
  name               = "${local.name_prefix}-glue-transform-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume_role.json
}

data "aws_iam_policy_document" "glue_transform" {
  statement {
    sid = "ListDataLake"
    actions = [
      "s3:GetBucketLocation",
      "s3:ListBucket",
    ]
    resources = [aws_s3_bucket.data_lake.arn]
  }

  statement {
    sid = "ReadRawDataAndScript"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
    ]
    resources = [
      "${aws_s3_bucket.data_lake.arn}/raw/listings/*",
      aws_s3_object.glue_transform.arn,
    ]
  }

  statement {
    sid = "WriteProcessedListings"
    actions = [
      "s3:DeleteObject",
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = ["${aws_s3_bucket.data_lake.arn}/processed/listings/*"]
  }

  statement {
    sid = "WriteGlueLogs"
    actions = [
      "logs:AssociateKmsKey",
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws-glue/*"]
  }
}

resource "aws_iam_role_policy" "glue_transform" {
  name   = "transform-listings-data"
  role   = aws_iam_role.glue_transform.id
  policy = data.aws_iam_policy_document.glue_transform.json
}

# Glue cleans the source CSV and writes city-partitioned Parquet for analytics.
resource "aws_glue_job" "listings_transform" {
  name              = "${local.name_prefix}-listings-transform"
  description       = "Cleans Airbnb listings and writes city-partitioned Parquet"
  role_arn          = aws_iam_role.glue_transform.arn
  glue_version      = "5.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 10
  max_retries       = 0

  command {
    name            = "glueetl"
    python_version  = "3"
    script_location = "s3://${aws_s3_bucket.data_lake.id}/${aws_s3_object.glue_transform.key}"
  }

  default_arguments = {
    "--RAW_LISTINGS_URI"             = "s3://${aws_s3_bucket.data_lake.id}/raw/listings/Listings.csv"
    "--PROCESSED_LISTINGS_URI"       = "s3://${aws_s3_bucket.data_lake.id}/processed/listings/"
    "--enable-metrics"               = "true"
    "--enable-observability-metrics" = "true"
    "--job-language"                 = "python"
  }

  depends_on = [aws_iam_role_policy.glue_transform]
}

# The Glue catalog and Athena workgroup provide controlled SQL access.
resource "aws_glue_catalog_database" "analytics" {
  name        = replace("${local.name_prefix}-analytics", "-", "_")
  description = "Catalog for processed Airbnb market analytics"
}

resource "aws_glue_catalog_table" "listings" {
  name          = "listings"
  database_name = aws_glue_catalog_database.analytics.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"            = "parquet"
    "projection.enabled"        = "true"
    "projection.city.type"      = "enum"
    "projection.city.values"    = "Bangkok,Cape Town,Hong Kong,Istanbul,Mexico City,New York,Paris,Rio de Janeiro,Rome,Sydney"
    "storage.location.template" = "s3://${aws_s3_bucket.data_lake.id}/processed/listings/city=$${city}/"
  }

  partition_keys {
    name = "city"
    type = "string"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.data_lake.id}/processed/listings/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "neighbourhood"
      type = "string"
    }
    columns {
      name = "property_type"
      type = "string"
    }
    columns {
      name = "room_type"
      type = "string"
    }
    columns {
      name = "price"
      type = "double"
    }
    columns {
      name = "accommodates"
      type = "int"
    }
    columns {
      name = "bedrooms"
      type = "double"
    }
    columns {
      name = "minimum_nights"
      type = "int"
    }
    columns {
      name = "review_scores_rating"
      type = "double"
    }
    columns {
      name = "instant_bookable"
      type = "boolean"
    }
    columns {
      name = "host_is_superhost"
      type = "boolean"
    }
  }
}

resource "aws_athena_workgroup" "analytics" {
  name        = "${local.name_prefix}-analytics"
  description = "Governed workgroup for application market analytics"
  state       = "ENABLED"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
    bytes_scanned_cutoff_per_query     = 1073741824

    result_configuration {
      output_location = "s3://${aws_s3_bucket.data_lake.id}/analytics/query-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}
