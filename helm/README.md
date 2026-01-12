# Helm Quick Start

## Install Helm
```bash
brew install helm
```

## Setup

### 1. Edit values.yaml
```bash
# Set your Docker registry
vim helm/content-engine/values.yaml
# Change: imageRegistry: "your-registry.io"
```

### 2. Build & Push Images
```bash
# Build all services
./scripts/build-and-push.sh your-registry.io latest
```

### 3. Create Secrets
```bash
./scripts/setup-secrets.sh
```

### 4. Deploy
```bash
# Install everything
helm install content-engine ./helm/content-engine

# Or with custom namespace
helm install content-engine ./helm/content-engine -n content-engine --create-namespace
```

## Common Commands

```bash
# Upgrade after changing values.yaml
helm upgrade content-engine ./helm/content-engine

# Scale a service (edit values.yaml or override)
helm upgrade content-engine ./helm/content-engine \
  --set services.content-producer.replicas=10

# Disable a service
helm upgrade content-engine ./helm/content-engine \
  --set services.visual-composer.enabled=false

# Check what will deploy (dry-run)
helm install content-engine ./helm/content-engine --dry-run --debug

# View deployed resources
kubectl get all -n content-engine

# Logs
kubectl logs -l app=content-producer -n content-engine -f

# Uninstall
helm uninstall content-engine -n content-engine
```

## Environment-Specific Deploys

### values-dev.yaml
```yaml
global:
  environment: dev
services:
  content-producer:
    replicas: 1
```

### values-prod.yaml
```yaml
global:
  environment: production
  imageRegistry: prod-registry.io
postgres:
  storage: 100Gi
services:
  content-producer:
    replicas: 10
  management-api:
    serviceType: LoadBalancer
```

Deploy with:
```bash
helm install content-engine ./helm/content-engine -f helm/values-prod.yaml
```

## Key Helm Terms

- **Chart**: Package of K8s templates (your helm/content-engine/ folder)
- **Release**: Deployed instance of a chart
- **Values**: Configuration (values.yaml)
- **Template**: K8s manifest with {{ }} variables

## Workflow

1. Edit `values.yaml` (change replicas, enable/disable services, etc.)
2. Run `helm upgrade content-engine ./helm/content-engine`
3. Helm applies only what changed (smart updates)

That's it! One chart, all variation in values.yaml.
