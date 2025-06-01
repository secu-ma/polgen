# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

resource "aws_cognito_user_pool" "auth_pool" {
  name = "wiki_users-${local.seed_prefix}"

  admin_create_user_config {
    allow_admin_create_user_only = true
  }
}

resource "aws_cognito_user_pool_domain" "auth_domain" {
  domain       = "polgen-${local.seed_prefix}"
  user_pool_id = aws_cognito_user_pool.auth_pool.id
}

resource "aws_cognito_user_pool_client" "wiki_client" {
  name         = "wiki_client"
  user_pool_id = aws_cognito_user_pool.auth_pool.id

  generate_secret                      = true
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid"]
  supported_identity_providers         = ["COGNITO"]
  callback_urls                        = ["https://${aws_cloudfront_distribution.wiki_distribution.domain_name}"]
}

# Optional user account
resource "aws_cognito_user" "default_user" {
  count = var.email != "" ? 1 : 0

  user_pool_id = aws_cognito_user_pool.auth_pool.id
  username     = var.email

  attributes = {
    email          = var.email
    email_verified = false
  }

  lifecycle {
    ignore_changes = [
      attributes["email_verified"]
    ]
  }
}
