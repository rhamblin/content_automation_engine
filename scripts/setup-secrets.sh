#!/bin/bash
set -e

NAMESPACE="content-engine"

echo "Setting up secrets in namespace: $NAMESPACE"
echo "============================================"

kubectl create namespace $NAMESPACE 2>/dev/null || echo "Namespace exists"

echo "Creating secrets..."

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

echo ""
echo "⚠️  Database credentials - edit with real values!"
kubectl create secret generic db-credentials \
  --from-literal=POSTGRES_USER=${POSTGRES_USER:-postgres} \
  --from-literal=POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-changeme} \
  --from-literal=POSTGRES_DB_NAME=${POSTGRES_DB_NAME:-content_engine} \
  --from-literal=APP_DB_USER=${APP_DB_USER:-app_user} \
  --from-literal=APP_DB_PASSWORD=${APP_DB_PASSWORD:-changeme} \
  --from-literal=ANALYTICS_DB_USER=${ANALYTICS_DB_USER:-analytics_user} \
  --from-literal=ANALYTICS_DB_PASSWORD=${ANALYTICS_DB_PASSWORD:-changeme} \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "✓ Secrets ready!"
echo ""
echo "View: kubectl get secrets -n $NAMESPACE"
