variable "aws_region" {
  description = "AWS region used by the project."
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Stable project prefix used for state resources."
  type        = string
  default     = "airbnb-market-intelligence"
}
