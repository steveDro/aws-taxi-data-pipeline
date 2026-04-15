# ──────────────────────────────────────────
# Variables
# ──────────────────────────────────────────

variable "region" {
  description = "AWS region for the resources"
  type        = string
  default     = "us-east-1"
}

variable "redshift_username" {
  description = "Redshift master username"
  type        = string
  default     = "admin"
}

variable "redshift_password" {
  description = "Redshift master password"
  type        = string
  sensitive   = true
}
