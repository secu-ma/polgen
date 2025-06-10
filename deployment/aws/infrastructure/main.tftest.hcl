run "test" {
  override_resource {
    target = aws_cloudfront_distribution.wiki_distribution
  }
}
