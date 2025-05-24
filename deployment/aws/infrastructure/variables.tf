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
