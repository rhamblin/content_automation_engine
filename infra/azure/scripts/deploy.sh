#!/usr/bin/env bash
# deploy.sh — Full deployment orchestrator for Azure Container Apps.
#
# Usage:
#   ./deploy.sh --postgres-password <pw> [--init-db] [--seed]
#
# Prerequisites: az cli logged in, Docker running

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/.."
PROJECT_ROOT="${INFRA_DIR}/../.."

# ─── Parse arguments ───────────────────────────────────────────
PG_PASSWORD=""
INIT_DB=false
RUN_SEED=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --postgres-password) PG_PASSWORD="$2"; shift 2 ;;
    --init-db) INIT_DB=true; shift ;;
    --seed) RUN_SEED=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "${PG_PASSWORD}" ]]; then
  echo "Error: --postgres-password is required"
  exit 1
fi

ENV="dev"
LOCATION="canadacentral"

echo "============================================"
echo " Content Engine — Azure Deployment (${ENV})"
echo "============================================"

# ─── 1. Deploy infrastructure (no Container Apps yet) ─────────
echo ""
echo "==> Phase 1: Deploying infrastructure (ACR, PG, Redis, Storage, Foundry, KV, CAE)..."
INFRA_OUTPUT=$(az deployment sub create \
  --location "${LOCATION}" \
  --parameters "${INFRA_DIR}/parameters/${ENV}.bicepparam" \
  --parameters postgresAdminPassword="${PG_PASSWORD}" \
  --parameters deployApps=false \
  --query properties.outputs \
  --output json)

# Extract outputs from infra phase
ACR_LOGIN_SERVER=$(echo "${INFRA_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['acrLoginServer']['value'])")
RG_NAME=$(echo "${INFRA_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['resourceGroupName']['value'])")
KV_NAME=$(echo "${INFRA_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['keyVaultName']['value'])")
PG_FQDN=$(echo "${INFRA_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['postgresFqdn']['value'])")
DEFAULT_DOMAIN=$(echo "${INFRA_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['defaultDomain']['value'])")

echo "    Resource Group:    ${RG_NAME}"
echo "    ACR:               ${ACR_LOGIN_SERVER}"
echo "    Key Vault:         ${KV_NAME}"
echo "    PostgreSQL FQDN:   ${PG_FQDN}"

# ─── 2. Login to ACR ──────────────────────────────────────────
echo ""
echo "==> Logging in to ACR..."
az acr login --name "${ACR_LOGIN_SERVER%%.*}"

# ─── 3. Build and push Docker images ──────────────────────────
echo ""
echo "==> Building and pushing Docker images..."

SERVICES=(
  "management-api:services/management-api/Dockerfile:services/management-api"
  "template-service:services/template-service/Dockerfile:services/template-service"
  "promotion-orchestrator:services/promotion-orchestrator/Dockerfile:services/promotion-orchestrator"
  "scheduler:services/scheduler/Dockerfile:services/scheduler"
  "channel-worker:services/channel-worker/Dockerfile:services/channel-worker"
  "activity-reporter:services/activity-reporter/Dockerfile:services/activity-reporter"
  "analytics-collector:services/analytics-collector/Dockerfile:services/analytics-collector"
  "seed-worker:services/seed-worker/Dockerfile:services/seed-worker"
)

for svc_spec in "${SERVICES[@]}"; do
  IFS=: read -r IMAGE DOCKERFILE CONTEXT <<< "${svc_spec}"
  echo "    Building ${IMAGE}..."
  docker build \
    -t "${ACR_LOGIN_SERVER}/${IMAGE}:latest" \
    -f "${PROJECT_ROOT}/${DOCKERFILE}" \
    "${PROJECT_ROOT}/${CONTEXT}"
  docker push "${ACR_LOGIN_SERVER}/${IMAGE}:latest"
done

# Build frontend with VITE_ build args
echo "    Building frontend..."
VITE_CLIENT_ID=$(az keyvault secret show --vault-name "${KV_NAME}" --name "azure-entra-client-id" --query value --output tsv 2>/dev/null || echo "")
VITE_TENANT_ID=$(az keyvault secret show --vault-name "${KV_NAME}" --name "azure-entra-tenant-id" --query value --output tsv 2>/dev/null || echo "")
API_URL="https://content-engine-${ENV}-management-api.${DEFAULT_DOMAIN}"

docker build \
  --build-arg VITE_MANAGEMENT_API_URL="${API_URL}" \
  --build-arg VITE_AZURE_CLIENT_ID="${VITE_CLIENT_ID}" \
  --build-arg VITE_AZURE_TENANT_ID="${VITE_TENANT_ID}" \
  -t "${ACR_LOGIN_SERVER}/frontend:latest" \
  -f "${PROJECT_ROOT}/frontend/Dockerfile" \
  "${PROJECT_ROOT}/frontend"
docker push "${ACR_LOGIN_SERVER}/frontend:latest"

# ─── 4. Deploy Container Apps (images now exist in ACR) ───────
echo ""
echo "==> Phase 2: Deploying Container Apps..."
DEPLOY_OUTPUT=$(az deployment sub create \
  --location "${LOCATION}" \
  --parameters "${INFRA_DIR}/parameters/${ENV}.bicepparam" \
  --parameters postgresAdminPassword="${PG_PASSWORD}" \
  --parameters deployApps=true \
  --query properties.outputs \
  --output json)

API_URL=$(echo "${DEPLOY_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['managementApiUrl']['value'])")
FRONTEND_URL=$(echo "${DEPLOY_OUTPUT}" | python3 -c "import sys,json; print(json.load(sys.stdin)['frontendUrl']['value'])")

# ─── 6. Optional: Init database ───────────────────────────────
if [[ "${INIT_DB}" == "true" ]]; then
  echo ""
  echo "==> Initializing database..."
  "${SCRIPT_DIR}/init-database.sh" "${PG_FQDN}" "pgadmin" "${PG_PASSWORD}" "contentengine_${ENV}"
fi

# ─── 7. Optional: Trigger seed worker ─────────────────────────
if [[ "${RUN_SEED}" == "true" ]]; then
  echo ""
  echo "==> Triggering seed-worker job..."
  az containerapp job start \
    --name "content-engine-${ENV}-seed-worker" \
    --resource-group "${RG_NAME}"
fi

echo ""
echo "============================================"
echo " Deployment complete!"
echo "============================================"
echo "  Management API: ${API_URL}"
echo "  Frontend:       ${FRONTEND_URL}"
echo "  Health check:   ${API_URL}/health"
echo "============================================"
