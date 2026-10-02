# Private Lambda networking spans two availability zones without a NAT Gateway.
data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "lambda" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
}

resource "aws_subnet" "lambda_private" {
  for_each = {
    a = {
      availability_zone = data.aws_availability_zones.available.names[0]
      cidr_block        = "10.20.1.0/24"
    }
    b = {
      availability_zone = data.aws_availability_zones.available.names[1]
      cidr_block        = "10.20.2.0/24"
    }
  }

  vpc_id                  = aws_vpc.lambda.id
  availability_zone       = each.value.availability_zone
  cidr_block              = each.value.cidr_block
  map_public_ip_on_launch = false
}

resource "aws_route_table" "lambda_private" {
  for_each = aws_subnet.lambda_private
  vpc_id   = aws_vpc.lambda.id
}

resource "aws_route_table_association" "lambda_private" {
  for_each       = aws_subnet.lambda_private
  subnet_id      = each.value.id
  route_table_id = aws_route_table.lambda_private[each.key].id
}

resource "aws_security_group" "lambda" {
  name        = "${local.name_prefix}-lambda"
  description = "Outbound HTTPS from private Lambda functions"
  vpc_id      = aws_vpc.lambda.id

  egress {
    description = "HTTPS to interface endpoints inside the application VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.lambda.cidr_block]
  }

  egress {
    description = "HTTPS to S3 and DynamoDB gateway endpoints"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    prefix_list_ids = [
      aws_vpc_endpoint.s3.prefix_list_id,
      aws_vpc_endpoint.dynamodb.prefix_list_id,
    ]
  }
}

resource "aws_security_group" "endpoint" {
  name        = "${local.name_prefix}-vpc-endpoints"
  description = "PrivateLink ingress from Lambda security group"
  vpc_id      = aws_vpc.lambda.id

  ingress {
    description     = "HTTPS from private Lambda functions"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }
}

# Gateway endpoints keep S3 and DynamoDB traffic on the AWS network without NAT.
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.lambda.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [for route_table in aws_route_table.lambda_private : route_table.id]
}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.lambda.id
  service_name      = "com.amazonaws.${var.aws_region}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [for route_table in aws_route_table.lambda_private : route_table.id]
}

# These interface endpoints cover Lambda logging, Athena queries, and Bedrock chat.
resource "aws_vpc_endpoint" "interface" {
  for_each = toset([
    "logs",
    "athena",
    "bedrock-runtime",
  ])

  vpc_id              = aws_vpc.lambda.id
  service_name        = "com.amazonaws.${var.aws_region}.${each.key}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [for subnet in aws_subnet.lambda_private : subnet.id]
  security_group_ids  = [aws_security_group.endpoint.id]
  private_dns_enabled = true
}

data "aws_iam_policy_document" "lambda_vpc_access" {
  statement {
    sid = "ManageLambdaNetworkInterfaces"
    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "lambda_vpc_access" {
  for_each = {
    health     = aws_iam_role.health_lambda
    prediction = aws_iam_role.prediction_lambda
    analytics  = aws_iam_role.analytics_lambda
    history    = aws_iam_role.history_lambda
    chat       = aws_iam_role.chat_lambda
  }

  name   = "lambda-vpc-network-interfaces"
  role   = each.value.id
  policy = data.aws_iam_policy_document.lambda_vpc_access.json
}

locals {
  lambda_private_subnet_ids = [for subnet in aws_subnet.lambda_private : subnet.id]
}

output "lambda_vpc_id" {
  description = "VPC used by the private Lambda functions."
  value       = aws_vpc.lambda.id
}

output "lambda_private_subnet_ids" {
  description = "Private subnet IDs used by the Lambda functions."
  value       = local.lambda_private_subnet_ids
}
