# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = var.state_bucket != "" ? var.state_bucket : "state-${substr(sha256(var.unique_seed), 0, 16)}"
    key    = var.state_key != "" ? var.state_key : "terraform.tfstate"
  }
}

# Let the default provider be configured with environment variables from the workflow:
#  AWS_ACCESS_KEY_ID
#  AWS_SECRET_ACCESS_KEY
#  AWS_SESSION_TOKEN (optionally)
#  AWS_REGION
provider "aws" {
}

# Specific provider for us-east-1 (needed for lambda@edge)
provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"
}

data "aws_region" "current" {}
