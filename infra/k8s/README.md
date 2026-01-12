# Kubernetes Infrastructure Files

These are standalone Kubernetes manifests for supporting infrastructure.

## Files

- **namespace.yaml** - Creates `content-automation` namespace
- **configmap.yaml** - Shared non-sensitive configuration
- **secrets.yaml** - PostgreSQL credentials (base64 encoded)

## Quick Start

### Apply All Infrastructure

```bash
# Create namespace, configmap, and secrets
kubectl apply -f infra/k8s/
```

### Apply Individually

```bash
# In order
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
kubectl apply -f infra/k8s/secrets.yaml
```

## Verify

```bash
# Check namespace
kubectl get namespace content-automation

# Check configmap
kubectl get configmap -n content-automation
kubectl describe configmap shared-config -n content-automation

# Check secrets
kubectl get secrets -n content-automation
kubectl describe secret postgres-credentials -n content-automation

# View secret values (decoded)
kubectl get secret postgres-credentials -n content-automation -o jsonpath='{.data.POSTGRES_USER}' | base64 -d
```

## Using in Deployments

### Load All ConfigMap Values

```yaml
spec:
  containers:
  - name: my-service
    envFrom:
    - configMapRef:
        name: shared-config
```

## Clean Up

```bash
# Delete all
kubectl delete -f infra/k8s/
```
