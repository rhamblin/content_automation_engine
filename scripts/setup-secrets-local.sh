#!/bin/bash
set -e

NAMESPACE="content-engine"

echo "Setting up LOCAL secrets in namespace: $NAMESPACE"
echo "=================================================="

kubectl create namespace $NAMESPACE 2>/dev/null || echo "Namespace exists"

# Use local secret files (checked into Git or local only)
kubectl create secret generic openai-api-key \
  --from-file=key=./secrets/openai-api-key.txt \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic azure-blob-storage \
  --from-file=connection-string=./secrets/azure-blob-storage-connection-string.txt \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic azure-foundry-api-key \
  --from-file=key=./secrets/azure-foundry-proj-default-api-key.txt \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# Local dev database credentials (weak passwords OK)
kubectl create secret generic db-credentials \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=dev123 \
  --from-literal=POSTGRES_DB_NAME=content_engine_dev \
  --from-literal=APP_DB_USER=app_user \
  --from-literal=APP_DB_PASSWORD=dev123 \
  --from-literal=ANALYTICS_DB_USER=analytics_user \
  --from-literal=ANALYTICS_DB_PASSWORD=dev123 \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "✓ Local secrets created!"
