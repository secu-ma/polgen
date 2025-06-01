# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

data "archive_file" "check_auth_archive" {
  type        = "zip"
  output_path = ".build/check_auth_archive.zip"
  source {
    content  = <<EOF

exports.handler = (event, context, callback) => {
  const response = {
    status: '200',
    statusDescription: 'OK',
    headers: {
      'cache-control': [{
        key: 'Cache-Control',
        value: 'max-age=100'
      }],
      'content-type': [{
        key: 'Content-Type',
        value: 'text/html'
      }]
    },
    body: '<p>Infrastructure for Wiki is deployed. Now deploy a real version using deploy.py.</p>'
  };
  callback(null, response);
}

EOF
    filename = "bundle.js"
  }
}

resource "aws_lambda_function" "check_auth" {
  provider = aws.us-east-1

  function_name = "wiki-check-auth-${local.seed_prefix}"
  role          = aws_iam_role.edge_lambda_role.arn
  runtime       = "nodejs20.x"
  handler       = "bundle.handler"

  filename         = data.archive_file.check_auth_archive.output_path
  source_code_hash = data.archive_file.check_auth_archive.output_base64sha256

  publish = true

  lifecycle {
    ignore_changes = [
      source_code_hash,
    ]
  }
}
