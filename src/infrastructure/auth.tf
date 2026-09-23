resource "aws_cognito_user_pool" "users" {
  name                     = "${local.name_prefix}-users"
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  deletion_protection      = "INACTIVE"
  mfa_configuration        = "OFF"

  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    require_uppercase                = true
    temporary_password_validity_days = 3
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
  }

  user_attribute_update_settings {
    attributes_require_verification_before_update = ["email"]
  }
}

resource "aws_cognito_user_pool_client" "frontend" {
  name         = "${local.name_prefix}-frontend"
  user_pool_id = aws_cognito_user_pool.users.id

  generate_secret                      = false
  prevent_user_existence_errors        = "ENABLED"
  supported_identity_providers         = ["COGNITO"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  callback_urls                        = ["https://${aws_cloudfront_distribution.frontend.domain_name}/"]
  logout_urls                          = ["https://${aws_cloudfront_distribution.frontend.domain_name}/"]
  explicit_auth_flows                  = ["ALLOW_REFRESH_TOKEN_AUTH"]
  enable_token_revocation              = true
  access_token_validity                = 1
  id_token_validity                    = 1
  refresh_token_validity               = 30

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
}

resource "aws_cognito_user_pool_domain" "users" {
  domain       = "${local.name_prefix}-${random_id.bucket_suffix.hex}"
  user_pool_id = aws_cognito_user_pool.users.id
}

resource "aws_apigatewayv2_authorizer" "users" {
  api_id           = aws_apigatewayv2_api.platform.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "${local.name_prefix}-cognito-authorizer"

  jwt_configuration {
    audience = [aws_cognito_user_pool_client.frontend.id]
    issuer   = "https://cognito-idp.${var.aws_region}.amazonaws.com/${aws_cognito_user_pool.users.id}"
  }
}

resource "aws_s3_object" "auth_config" {
  bucket = aws_s3_bucket.frontend.id
  key    = "auth-config.js"
  content = format(
    "window.AUTH_CONFIG = Object.freeze({ clientId: %s, domain: %s, redirectUri: %s, logoutUri: %s });",
    jsonencode(aws_cognito_user_pool_client.frontend.id),
    jsonencode("https://${aws_cognito_user_pool_domain.users.domain}.auth.${var.aws_region}.amazoncognito.com"),
    jsonencode("https://${aws_cloudfront_distribution.frontend.domain_name}/"),
    jsonencode("https://${aws_cloudfront_distribution.frontend.domain_name}/")
  )
  content_type  = "application/javascript; charset=utf-8"
  cache_control = "no-cache"
}
