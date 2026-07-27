data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_ssm_parameter" "ela_api_arn" {
  name            = var.ela_api_arn_parameter_name
  with_decryption = false
}

data "aws_cloudfront_cache_policy" "caching_optimized" {
  name = "Managed-CachingOptimized"
}

data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host_header" {
  name = "Managed-AllViewerExceptHostHeader"
}

locals {
  account_id           = data.aws_caller_identity.current.account_id
  region               = data.aws_region.current.region
  name                 = "iisd-ela-seasonality"
  lambda_function_name = "${local.name}-api"
  artifact_bucket_name = "${local.name}-artifacts-${local.account_id}"
  static_bucket_name   = "${local.name}-static-${local.account_id}"
  static_origin_id     = "${local.name}-static"
  api_origin_id        = "${local.name}-api"
  lambda_zip_path      = abspath("${path.module}/${var.lambda_zip_path}")
  static_dir           = abspath("${path.module}/${var.static_site_path}")
  static_files         = fileset(local.static_dir, "**/*")
  ela_api_id           = element(reverse(split("/", data.aws_ssm_parameter.ela_api_arn.value)), 0)
  ela_api_base_url     = "https://${local.ela_api_id}.execute-api.${local.region}.amazonaws.com/${var.ela_api_stage_name}"
  frame_ancestors      = length(var.frame_ancestors) > 0 ? join(" ", var.frame_ancestors) : "'none'"

  content_types = {
    ".css"   = "text/css"
    ".html"  = "text/html"
    ".ico"   = "image/x-icon"
    ".jpeg"  = "image/jpeg"
    ".jpg"   = "image/jpeg"
    ".js"    = "application/javascript"
    ".json"  = "application/json"
    ".map"   = "application/json"
    ".png"   = "image/png"
    ".svg"   = "image/svg+xml"
    ".ttf"   = "font/ttf"
    ".txt"   = "text/plain"
    ".webp"  = "image/webp"
    ".woff"  = "font/woff"
    ".woff2" = "font/woff2"
  }
}
