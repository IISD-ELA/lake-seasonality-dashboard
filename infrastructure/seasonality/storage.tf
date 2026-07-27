resource "aws_s3_bucket" "artifacts" {
  bucket = local.artifact_bucket_name
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    id     = "expire-old-lambda-artifacts"
    status = "Enabled"

    filter {
      prefix = "lambda/"
    }

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }

  depends_on = [aws_s3_bucket_versioning.artifacts]
}

resource "aws_s3_object" "lambda" {
  bucket = aws_s3_bucket.artifacts.id
  key    = "lambda/${filebase64sha256(local.lambda_zip_path)}.zip"
  source = local.lambda_zip_path

  source_hash = filebase64sha256(local.lambda_zip_path)

  depends_on = [
    aws_s3_bucket_public_access_block.artifacts,
    aws_s3_bucket_server_side_encryption_configuration.artifacts,
  ]
}

resource "aws_s3_bucket" "static" {
  bucket = local.static_bucket_name
}

resource "aws_s3_bucket_public_access_block" "static" {
  bucket = aws_s3_bucket.static.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "static" {
  bucket = aws_s3_bucket.static.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "static" {
  bucket = aws_s3_bucket.static.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "static" {
  bucket = aws_s3_bucket.static.id

  rule {
    id     = "expire-old-static-asset-versions"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }

  depends_on = [aws_s3_bucket_versioning.static]
}

resource "aws_s3_object" "static" {
  for_each = local.static_files

  bucket       = aws_s3_bucket.static.id
  key          = each.value
  source       = "${local.static_dir}/${each.value}"
  source_hash  = filemd5("${local.static_dir}/${each.value}")
  content_type = lookup(local.content_types, lower(try(regex("\\.[^.]+$", each.value), "")), "application/octet-stream")

  cache_control = (
    contains(["index.html", "app.js", "styles.css"], each.value)
    ? "no-cache"
    : startswith(each.value, "assets/") || startswith(each.value, "vendor/")
    ? "public, max-age=31536000, immutable"
    : "public, max-age=300"
  )

  depends_on = [
    aws_s3_bucket_ownership_controls.static,
    aws_s3_bucket_public_access_block.static,
  ]
}
