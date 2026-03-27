@description('Azure Key Vault for storing secrets')
param name string
param location string
param tags object = {}
param managedIdentityPrincipalId string

@secure()
param databaseUrl string
@secure()
param redisUrl string
@secure()
param blobStorageConnectionString string
@secure()
param foundryApiKey string
param foundryEndpoint string

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    tenantId: subscription().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    accessPolicies: [
      {
        tenantId: subscription().tenantId
        objectId: managedIdentityPrincipalId
        permissions: {
          secrets: [
            'get'
            'list'
          ]
        }
      }
    ]
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

resource secretDatabaseUrl 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'database-url'
  properties: {
    value: databaseUrl
  }
}

resource secretRedisUrl 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'redis-url'
  properties: {
    value: redisUrl
  }
}

resource secretBlobStorage 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'blob-storage-connection-string'
  properties: {
    value: blobStorageConnectionString
  }
}

// Auto-populated from Foundry module
resource secretAzureFoundryApiKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-foundry-api-key'
  properties: {
    value: foundryApiKey
  }
}

resource secretAzureFoundryEndpoint 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-foundry-endpoint'
  properties: {
    value: foundryEndpoint
  }
}

// Placeholder secrets — set real values via deploy script or Azure Portal
resource secretOpenaiApiKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'openai-api-key'
  properties: {
    value: 'REPLACE_ME'
  }
}

resource secretEntraClientSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'azure-entra-client-secret'
  properties: {
    value: 'REPLACE_ME'
  }
}

resource secretRefreshTokenKey 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'refresh-token-encryption-key'
  properties: {
    value: 'REPLACE_ME'
  }
}

resource secretPinterestAppId 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'pinterest-app-id'
  properties: {
    value: 'REPLACE_ME'
  }
}

resource secretPinterestAppSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'pinterest-app-secret'
  properties: {
    value: 'REPLACE_ME'
  }
}

@description('Key Vault URI')
output vaultUri string = keyVault.properties.vaultUri

@description('Key Vault name')
output vaultName string = keyVault.name
