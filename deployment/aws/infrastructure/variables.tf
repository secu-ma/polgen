variable "unique_seed" {
  type = string
  default = ""
  description = "A unique seed for this specific wiki instance. Used by some resources that require a unique name such as the state backend S3 bucket."
}

variable "state_bucket" {
  type = string
  default = ""
  description = "The name of the bucket where Tofu state will be stored"
  validation {
    condition = var.state_bucket != "" || var.unique_seed != ""
    error_message = "Either provide state_bucket or unique_seed variable"
  }
}

variable "state_key" {
  type = string
  default = ""
  description = "The key where Tofu state will be stored"
}

variable "custom_domain" {
  type = string
  default = ""
  description = "A custom domain name for this distribution. This requires additional DNS configuration. Read the docs."
}

variable "email" {
  type = string
  default = ""
  description = "A user with this email address is created and an invite email is sent to complete registration"

  validation {
    condition     = var.email == "" || can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.email))
    error_message = "Please provide a valid email address."
  }
}
