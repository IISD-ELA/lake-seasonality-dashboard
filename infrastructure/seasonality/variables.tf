variable "aws_region" {
  type    = string
  default = "ca-central-1"
}

variable "aws_profile" {
  type    = string
  default = "iisd"
}

variable "lambda_zip_path" {
  type    = string
  default = "../../build/lambda.zip"
}

variable "static_site_path" {
  type    = string
  default = "../../build/site"
}

variable "ela_api_arn_parameter_name" {
  type    = string
  default = "/iisd-ela/config/ela-api/arn"
}

variable "ela_api_stage_name" {
  type    = string
  default = "dev"
}

variable "frame_ancestors" {
  description = "CSP sources allowed to embed the dashboard; an empty list denies framing."
  type        = list(string)
  default     = ["'self'", "https://www.iisd.org"]
}

variable "alarm_sns_topic_arn" {
  description = "Optional SNS topic for upstream failure alarm and recovery notifications."
  type        = string
  default     = null
  nullable    = true
}
