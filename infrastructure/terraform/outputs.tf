output "deployment_context" {
  description = "Validated inputs for future provider-specific modules."
  value = {
    name_prefix     = local.name_prefix
    environment     = var.environment
    region          = var.region
    domain_name     = var.domain_name
    enable_langflow = var.enable_langflow
    images          = local.images
    tags            = local.common_tags
  }
}
