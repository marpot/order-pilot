# OrderPilot Helm chart

The chart packages the same small application topology as the plain manifests. It references an existing Kubernetes secret and never renders secret values.

```bash
helm lint infrastructure/helm
helm upgrade --install orderpilot infrastructure/helm --namespace orderpilot --create-namespace
```

Before installation, create the `orderpilot-secrets` secret described in `../kubernetes/README.md` and replace the example image repositories. Enable Langflow with `--set langflow.enabled=true` only after adding its password, flow ID, and API key to that secret.

For a production environment, prefer managed PostgreSQL and persistent Langflow storage. Those choices are intentionally not guessed by this provider-neutral chart.
