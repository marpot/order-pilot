# Kubernetes manifests

These manifests are a small deployment baseline, not a managed-cloud deployment. Replace the example image names before applying them.

Create secrets out of band:

```bash
kubectl create namespace orderpilot
kubectl -n orderpilot create secret generic orderpilot-secrets \
  --from-literal=postgres-user=orderpilot \
  --from-literal=postgres-password='replace-me' \
  --from-literal=postgres-db=orderpilot \
  --from-literal=langflow-superuser-password='replace-me'
```

Apply the core stack with `kubectl apply -k infrastructure/kubernetes/`. Apply `langflow.yaml` separately when AI orchestration is required. Enable `LANGFLOW_ENABLED` and add the optional flow ID/API key secret fields only after a validated flow exists.

The frontend uses its Vite proxy to reach the backend service. Expose `orderpilot-frontend` through the ingress or load balancer chosen for the target cluster. TLS, ingress controller, storage class, external PostgreSQL, backups, and image registry credentials remain environment-specific decisions.
