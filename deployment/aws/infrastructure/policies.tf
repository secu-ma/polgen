data "aws_iam_policy_document" "wiki_bucket_policy" {
  statement {
    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.wiki.arn}/*"
    ]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test = "StringEquals"
      values = [
        aws_cloudfront_distribution.wiki_distribution.arn
      ]
      variable = "AWS:SourceArn"
    }
  }

  # statement {
  #   actions = [
  #     "s3:ListBucket"
  #   ]
  #
  #   resources = [
  #     aws_s3_bucket.wiki.bucket
  #   ]
  #
  #   principals {
  #     identifiers = [
  #       aws_cloudfront_origin_access_identity.origin_access_identity.iam_arn
  #     ]
  #     type        = "AWS"
  #   }
  # }
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type = "Service"
      identifiers = [
        "lambda.amazonaws.com",
        "edgelambda.amazonaws.com",
      ]
    }

    actions = ["sts:AssumeRole"]
  }
}
