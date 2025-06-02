# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

output "cloudfront" {
  value = {
    id     = aws_cloudfront_distribution.wiki_distribution.id
    domain = "https://${aws_cloudfront_distribution.wiki_distribution.domain_name}"
  }
  description = "The domain where your wiki is deployed"
}

output "cognito" {
  value = {
    region         = data.aws_region.current.name
    userPoolId     = aws_cognito_user_pool.auth_pool.id
    userPoolAppId  = aws_cognito_user_pool_client.wiki_client.id
    userPoolDomain = "${aws_cognito_user_pool_domain.auth_domain.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
  }
  description = "The Cognito config"
}

output "cognito_client_secret" {
  value       = aws_cognito_user_pool_client.wiki_client.client_secret
  description = "The Cognito client secret"
  sensitive   = true
}

output "wiki_bucket" {
  value       = aws_s3_bucket.wiki.bucket
  description = "The bucket name where the wiki content is stored"
}
