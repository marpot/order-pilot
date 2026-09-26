locals {
  name_prefix = "orderpilot-${var.environment}"
  common_tags = {
    application = "orderpilot"
    environment = var.environment
    managed_by  = "terraform"
  }
  images = {
    backend  = "${var.image_registry}/orderpilot-backend"
    frontend = "${var.image_registry}/orderpilot-frontend"
  }
}

# Provider-specific networking, Kubernetes, managed PostgreSQL, DNS, and secret
# resources belong in modules added after the target cloud and operating model
# are selected. This provider-neutral root intentionally creates no resources.
