# Complete Helm Chart Example

## Structure
```
helm/content-engine/
├── Chart.yaml                    # Chart metadata
├── values.yaml                   # Base configuration
├── values-local.yaml             # Local dev overrides
├── values-prod.yaml              # Production overrides
└── templates/
    ├── _helpers.tpl              # Template helpers
    ├── namespace.yaml            # Namespace
    ├── configmap.yaml            # Shared env vars
    ├── redis.yaml                # Redis infrastructure
    ├── postgres.yaml             # PostgreSQL infrastructure
    └── microservices.yaml        # ALL services (loops through)
```

## How It Works

### 1. Chart.yaml
Defines chart metadata:
```yaml
apiVersion: v2
name: content-engine
version: 0.1.0
```

### 2. values.yaml
Defines ALL services in one place:
```yaml
services:
  content-producer:
    enabled: true
    replicas: 3
    image: content-producer
    port: 8002
    # ...
  visual-composer:
    enabled: true
    replicas: 2
    image: visual-composer
    # ...
```

### 3. templates/microservices.yaml
**ONE template loops through ALL services:**
```yaml
{{- range $name, $service := .Values.services }}
{{- if $service.enabled }}
---
# Creates Deployment for this service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ $name }}
spec:
  replicas: {{ $service.replicas }}
  # ... uses values from $service
---
# Creates Service for this service
apiVersion: v1
kind: Service
metadata:
  name: {{ $name }}
spec:
  ports:
  - port: {{ $service.port }}
{{- end }}
{{- end }}
```

## Deployment Scenarios

### Local Development (host.docker.internal)

```bash
# Run PostgreSQL and Redis on host machine
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres
docker run -d -p 6379:6379 redis

# Deploy to K8s, connect to host databases
helm install content-engine ./helm/content-engine \
  -f helm/content-engine/values-local.yaml
```

**values-local.yaml sets:**
- `DB_HOST: host.docker.internal` (connects to host)
- `redis.enabled: false` (use host Redis)
- `postgres.enabled: false` (use host PostgreSQL)
- `replicas: 1` for all services (saves resources)

### Production (in-cluster)

```bash
# Deploy everything to cluster
helm install content-engine ./helm/content-engine \
  -f helm/content-engine/values-prod.yaml
```

**values-prod.yaml sets:**
- `DB_HOST: postgres` (uses K8s service)
- `redis.enabled: true` (deploy Redis in cluster)
- `postgres.enabled: true` (deploy PostgreSQL in cluster)
- `replicas: 10` for high-load services

## Usage Examples

### Install
```bash
# Base install
helm install content-engine ./helm/content-engine

# Local dev
helm install content-engine ./helm/content-engine \
  -f helm/content-engine/values-local.yaml

# Production
helm install content-engine ./helm/content-engine \
  -f helm/content-engine/values-prod.yaml
```

### Update Configuration
```bash
# Edit values.yaml, then:
helm upgrade content-engine ./helm/content-engine

# Scale a specific service
helm upgrade content-engine ./helm/content-engine \
  --set services.content-producer.replicas=20

# Disable a service
helm upgrade content-engine ./helm/content-engine \
  --set services.visual-composer.enabled=false
```

### Validate Before Deploy
```bash
# See what will be deployed (dry-run)
helm install content-engine ./helm/content-engine --dry-run --debug

# Lint the chart
helm lint ./helm/content-engine

# Generate templates only
helm template content-engine ./helm/content-engine
```

### Manage Releases
```bash
# List releases
helm list

# Check status
helm status content-engine

# View deployed values
helm get values content-engine

# View history
helm history content-engine

# Rollback
helm rollback content-engine 1
```

## How Services Connect to PostgreSQL

Services automatically get these env vars from ConfigMap:
```
DB_HOST=postgres              # or host.docker.internal in local
DB_PORT=5432
POSTGRES_DB_NAME=xxx          # from secret
APP_DB_USER=xxx               # from secret
APP_DB_PASSWORD=xxx           # from secret
```

Your app constructs connection string:
```python
db_url = f"postgresql://{APP_DB_USER}:{APP_DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB_NAME}"
```

## Complete Workflow

### 1. Setup
```bash
# Install Helm
brew install helm

# Install kubectl
brew install kubectl

# Start K8s (Docker Desktop, minikube, or kind)
```

### 2. Configure
```bash
# Edit registry in values.yaml
vim helm/content-engine/values.yaml
# Change: imageRegistry: "your-registry.io"
```

### 3. Build Images
```bash
./scripts/build-and-push.sh your-registry.io latest
```

### 4. Create Secrets
```bash
./scripts/setup-secrets.sh
```

### 5. Deploy

**Local dev:**
```bash
# Start databases on host
docker-compose up -d redis postgres

# Deploy services to K8s
helm install content-engine ./helm/content-engine \
  -f helm/content-engine/values-local.yaml
```

**Production:**
```bash
# Deploy everything to cluster
helm install content-engine ./helm/content-engine \
  -f helm/content-engine/values-prod.yaml
```

### 6. Monitor
```bash
# Watch pods
kubectl get pods -n content-engine -w

# Logs
kubectl logs -l app=content-producer -n content-engine -f

# Shell into pod
kubectl exec -it deployment/content-producer -n content-engine -- bash
```

### 7. Update
```bash
# Edit values.yaml
vim helm/content-engine/values.yaml

# Apply changes
helm upgrade content-engine ./helm/content-engine
```

## Key Advantages

✅ **One template for all services** - DRY principle
✅ **Environment-specific configs** - values-local.yaml, values-prod.yaml
✅ **Easy scaling** - Change one number in values.yaml
✅ **Enable/disable services** - Set enabled: false
✅ **Version control** - All configs in Git
✅ **Rollback support** - helm rollback
✅ **Validation** - helm lint, dry-run before deploy

## Quick Reference

| Task | Command |
|------|---------|
| Install | `helm install content-engine ./helm/content-engine` |
| Upgrade | `helm upgrade content-engine ./helm/content-engine` |
| Uninstall | `helm uninstall content-engine` |
| Scale | `helm upgrade ... --set services.X.replicas=10` |
| Disable service | `helm upgrade ... --set services.X.enabled=false` |
| Dry-run | `helm install ... --dry-run --debug` |
| Rollback | `helm rollback content-engine` |
| Status | `helm status content-engine` |
| View pods | `kubectl get pods -n content-engine` |
| Logs | `kubectl logs -l app=SERVICE -n content-engine -f` |

That's the complete Helm setup!
