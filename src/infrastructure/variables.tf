# These inputs control the deployment region, naming, and environment.
variable "aws_region" {
  description = "AWS region used for regional resources."
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Short project identifier used in resource names and tags."
  type        = string
  default     = "airbnb-market-intelligence"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,31}$", var.project_name))
    error_message = "project_name must be 3 to 32 lowercase letters, numbers, or hyphens and start with a letter."
  }
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,11}$", var.environment))
    error_message = "environment must be 2 to 12 lowercase letters, numbers, or hyphens and start with a letter."
  }
}

variable "alert_email" {
  description = "Optional operator email for the encrypted SNS alert topic. The recipient must confirm the subscription."
  type        = string
  default     = null
  nullable    = true

  validation {
    condition     = var.alert_email == null || can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.alert_email))
    error_message = "alert_email must be null or a valid email address."
  }
}
