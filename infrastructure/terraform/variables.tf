variable "environment" {
  description = "Logical deployment environment name."
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "environment must be development, staging, or production."
  }
}

variable "region" {
  description = "Target region selected after a cloud provider is chosen."
  type        = string
  default     = "unset"
}

variable "image_registry" {
  description = "Container registry prefix for OrderPilot images."
  type        = string
  default     = "ghcr.io/your-org"
}

variable "domain_name" {
  description = "Optional public DNS name. DNS resources are not created by this foundation."
  type        = string
  default     = ""
}

variable "enable_langflow" {
  description = "Whether the future environment should provision Langflow capacity."
  type        = bool
  default     = false
}
