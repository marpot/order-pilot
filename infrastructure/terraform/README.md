# Terraform foundation

No cloud provider was selected, so this directory intentionally provisions no paid or provider-specific resources. It validates shared deployment inputs and establishes naming, image, and tagging conventions for a future environment module.

```bash
terraform -chdir=infrastructure/terraform init -backend=false
terraform -chdir=infrastructure/terraform validate
terraform -chdir=infrastructure/terraform plan -var-file=environments/example/terraform.tfvars.example
```

After selecting a provider, add focused modules for networking, a Kubernetes cluster or container runtime, managed PostgreSQL, a secret manager, registry access, DNS/TLS, and monitoring integration. Keep application secrets in the chosen secret manager and remote state in an encrypted backend. Do not commit `.tfvars` files containing credentials.
