#!/usr/bin/env bash
# setup-entra.sh — Create Azure Entra (Azure AD) app registration for the frontend SPA.
# Run once, then re-run only if auth config changes.
#
# Prerequisites: az cli logged in with sufficient permissions
# Usage: ./setup-entra.sh <key-vault-name> <management-api-url>

set -euo pipefail

KEYVAULT_NAME="${1:?Usage: $0 <key-vault-name> <management-api-url>}"
API_URL="${2:?Usage: $0 <key-vault-name> <management-api-url>}"

APP_NAME="content-engine-spa"
REDIRECT_URI="${API_URL}/auth/callback"

echo "==> Creating Entra app registration: ${APP_NAME}"

# Create app registration
APP_ID=$(az ad app create \
  --display-name "${APP_NAME}" \
  --sign-in-audience "AzureADMyOrg" \
  --web-redirect-uris "${REDIRECT_URI}" \
  --query appId \
  --output tsv)

echo "    App (client) ID: ${APP_ID}"

TENANT_ID=$(az account show --query tenantId --output tsv)
echo "    Tenant ID:       ${TENANT_ID}"

# Create client secret (valid for 1 year)
echo "==> Creating client secret"
CLIENT_SECRET=$(az ad app credential reset \
  --id "${APP_ID}" \
  --display-name "content-engine-secret" \
  --years 1 \
  --query password \
  --output tsv)

# Store in Key Vault
echo "==> Storing secrets in Key Vault: ${KEYVAULT_NAME}"
az keyvault secret set --vault-name "${KEYVAULT_NAME}" --name "azure-entra-client-id" --value "${APP_ID}" --output none
az keyvault secret set --vault-name "${KEYVAULT_NAME}" --name "azure-entra-client-secret" --value "${CLIENT_SECRET}" --output none
az keyvault secret set --vault-name "${KEYVAULT_NAME}" --name "azure-entra-tenant-id" --value "${TENANT_ID}" --output none

echo ""
echo "==> Entra app registration complete."
echo "    Use these values for the frontend build:"
echo "      VITE_AZURE_CLIENT_ID=${APP_ID}"
echo "      VITE_AZURE_TENANT_ID=${TENANT_ID}"
echo ""
echo "    Redirect URI configured: ${REDIRECT_URI}"
