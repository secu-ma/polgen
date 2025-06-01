# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

variable "unique_seed" {
  type        = string
  description = "A unique seed for this specific wiki instance. Used by some resources that require a unique name such as the state backend S3 bucket."
}

variable "state_key" {
  type        = string
  default     = ""
  description = "The key where Tofu state will be stored"
}

variable "custom_domain" {
  type        = string
  default     = ""
  description = "A custom domain name for this distribution. This requires additional DNS configuration. Read the docs."
}

variable "email" {
  type        = string
  default     = ""
  description = "A user with this email address is created and an invite email is sent to complete registration"

  validation {
    condition     = var.email == "" || can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.email))
    error_message = "Please provide a valid email address."
  }
}

variable "origin_path" {
  type = string
  default = ""
  description = "The path at S3 where the wiki app is deployed. Root if omitted."
}
