#!/bin/sh
set -e

# Normalize Docker secrets → env vars (local only)
# In production (Azure), env vars are set directly - no secret files

if [ -f /run/secrets/openai-api-key ]; then
  export OPENAI_API_KEY="$(cat /run/secrets/openai-api-key)"
fi

if [ -f /run/secrets/azure-blob-storage-connection-string ]; then
  export AZURE_BLOB_STORAGE_CONNECTION_STRING="$(cat /run/secrets/azure-blob-storage-connection-string)"
fi

if [ -f /run/secrets/azure-foundry-proj-default-api-key ]; then
  export AZURE_FOUNDRY_PROJ_DEFAULT_API_KEY="$(cat /run/secrets/azure-foundry-proj-default-api-key)"
fi

# Start the real process
exec "$@"
