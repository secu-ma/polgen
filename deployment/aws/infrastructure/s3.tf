resource "aws_s3_bucket" "wiki" {
  bucket_prefix = "wiki-"
}

resource "aws_s3_bucket_versioning" "wiki_versioning" {
  bucket = aws_s3_bucket.wiki.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "wiki_lifecycle" {
  bucket = aws_s3_bucket.wiki.id

  rule {
    id     = "LifeCycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 60
      storage_class   = "DEEP_ARCHIVE"
    }

    noncurrent_version_expiration {
      noncurrent_days = 120
    }
  }
}

resource "aws_s3_bucket_policy" "wiki_policy" {
  bucket = aws_s3_bucket.wiki.id
  policy = data.aws_iam_policy_document.wiki_bucket_policy.json
}

resource "aws_s3_bucket_public_access_block" "wiki_block" {
  bucket = aws_s3_bucket.wiki.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
