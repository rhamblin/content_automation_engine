#!/bin/bash
set -e

REGISTRY=${1:-"your-registry.io"}
TAG=${2:-"latest"}

SERVICES=(
  "management-api"
  "scheduler"
  "content-producer"
  "visual-composer"
  "promotion-orchestrator"
  "analytics-collector"
  "publication-worker"
  "activity-reporter"
  "template-service"
)

echo "Building and pushing to $REGISTRY:$TAG"
echo "========================================"

for service in "${SERVICES[@]}"; do
  echo ""
  echo "[$service] Building..."
  docker build -f docker/Dockerfile \
    --build-arg SERVICE_NAME=$service \
    -t $REGISTRY/$service:$TAG \
    .

  echo "[$service] Pushing..."
  docker push $REGISTRY/$service:$TAG
  echo "✓ $service done"
done

echo ""
echo "========================================"
echo "✓ All services ready!"
echo ""
echo "Next: helm upgrade --install content-engine ./helm/content-engine"
