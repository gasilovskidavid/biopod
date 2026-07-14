variable "aws_region" {
  type    = string
  default = "eu-west-3"
}

variable "alert_mail" {
  type = string
}

variable "my_ip" {
  type        = string
  description = "Admin source address in CIDR form, e.g. 203.0.113.7/32. Set in terraform.tfvars (gitignored)."

  validation {
    condition     = can(cidrnetmask(var.my_ip))
    error_message = "my_ip must be a CIDR block such as 203.0.113.7/32, not a bare IP address."
  }
}

variable "ssh_public_key" {
  type        = string
  description = "Public key content for admin SSH access. Set in terraform.tfvars (gitignored)."
}