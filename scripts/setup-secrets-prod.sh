#!/bin/bash
set -e

NAMESPACE="content-engine-prod"

echo "Setting up PRODUCTION secrets in namespace: $NAMESPACE"
echo "========================================================"

# Check required environment variables
required_vars=(
  "OPENAI_API_KEY"
  "AZURE_BLOB_STORAGE_CONNECTION_STRING"
  "AZURE_FOUNDRY_API_KEY"
  "POSTGRES_PASSWORD"
  "APP_DB_PASSWORD"
  "ANALYTICS_DB_PASSWORD"
)

for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ Error: $var environment variable not set"
    echo ""
    echo "Set all required variables first:"
    echo "  export OPENAI_API_KEY='sk-...'"
    echo "  export AZURE_BLOB_STORAGE_CONNECTION_STRING='...'"
    echo "  export AZURE_FOUNDRY_API_KEY='...'"
    echo "  export POSTGRES_PASSWORD='...'"
    echo "  export APP_DB_PASSWORD='...'"
    echo "  export ANALYTICS_DB_PASSWORD='...'"
    exit 1
  fi
done

kubectl create namespace $NAMESPACE 2>/dev/null || echo "Namespace exists"

echo "Creating secrets from environment variables..."

# NEVER use --from-file in production!
kubectl create secret generic openai-api-key \
  --from-literal=key=$OPENAI_API_KEY \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic azure-blob-storage \
  --from-literal=connection-string=$AZURE_BLOB_STORAGE_CONNECTION_STRING \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic azure-foundry-api-key \
  --from-literal=key=$AZURE_FOUNDRY_API_KEY \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic db-credentials \
  --from-literal=POSTGRES_USER=${POSTGRES_USER:-postgres} \
  --from-literal=POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
  --from-literal=POSTGRES_DB_NAME=${POSTGRES_DB_NAME:-content_engine_prod} \
  --from-literal=APP_DB_USER=${APP_DB_USER:-app_user} \
  --from-literal=APP_DB_PASSWORD=$APP_DB_PASSWORD \
  --from-literal=ANALYTICS_DB_USER=${ANALYTICS_DB_USER:-analytics_user} \
  --from-literal=ANALYTICS_DB_PASSWORD=$ANALYTICS_DB_PASSWORD \
  -n $NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "✓ Production secrets created securely!"
echo ""
echo "Verify: kubectl get secrets -n $NAMESPACE"
