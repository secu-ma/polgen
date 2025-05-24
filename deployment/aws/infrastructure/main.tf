terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
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
  alias = "us-east-1"
  region = "us-east-1"
}

data "aws_region" "current" {}
