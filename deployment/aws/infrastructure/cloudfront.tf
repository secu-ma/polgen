resource "aws_cloudfront_distribution" "wiki_distribution" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = var.custom_domain != "" ? [var.custom_domain] : []
  price_class         = "PriceClass_100"

  origin {
    domain_name              = aws_s3_bucket.wiki.bucket_domain_name
    origin_id                = "s3-wiki"
    origin_access_control_id = aws_cloudfront_origin_access_control.s3_access.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-wiki"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    cache_policy_id = aws_cloudfront_cache_policy.wiki_cache_policy.id

    lambda_function_association {
      event_type = "viewer-request"
      lambda_arn = aws_lambda_function.check_auth.qualified_arn
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  custom_error_response {
    error_caching_min_ttl = 10
    error_code            = 404
    response_code         = 404
    response_page_path    = "/404.html"
  }


  lifecycle {
    ignore_changes = [
      default_cache_behavior["lambda_function_association"],
    ]
  }
}

resource "aws_cloudfront_cache_policy" "wiki_cache_policy" {
  name        = "wiki-policy"
  default_ttl = 3600
  max_ttl     = 86400
  min_ttl     = 0


  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }
    headers_config {
      header_behavior = "none"
    }
    query_strings_config {
      query_string_behavior = "none"
    }
    enable_accept_encoding_gzip   = true
    enable_accept_encoding_brotli = true
  }
}

resource "aws_cloudfront_origin_access_control" "s3_access" {
  name                              = "wiki-access"
  description                       = "Access to wiki S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_function" "default_dir_object" {
  name    = "default_dir_object"
  runtime = "cloudfront-js-2.0"
  comment = "Replaces cloudfront subdir / requests with /index.html"
  publish = true
  code    = file("${path.module}/functions/default_dir_object.js")
}
