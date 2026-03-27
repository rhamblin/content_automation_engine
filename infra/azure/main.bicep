targetScope = 'subscription'

// ─── Parameters ───────────────────────────────────────────────
@description('Environment name (dev, stage, prod)')
param environment string

@description('Azure region')
param location string

@description('Project name used for resource naming')
param projectName string

@secure()
@description('PostgreSQL admin password')
param postgresAdminPassword string

@description('Region for AI Foundry (model availability varies by region)')
param foundryLocation string

@description('Deploy Container Apps (set false for infra-only phase before images are pushed)')
param deployApps bool = true

// ─── Derived Names ────────────────────────────────────────────
var resourceGroupName = 'rg-${projectName}-${environment}'
var baseName = '${projectName}-${environment}'
// ACR names must be alphanumeric only
var acrName = replace('acr${projectName}${environment}', '-', '')
// Storage account names: lowercase alphanumeric, 3-24 chars
var storageName = take(replace(toLower('st${projectName}${environment}'), '-', ''), 24)
var tags = {
  project: projectName
  environment: environment
}

// ─── Resource Group ───────────────────────────────────────────
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

// ─── Container Registry ───────────────────────────────────────
module acr 'modules/container-registry.bicep' = {
  scope: rg
  name: 'acr-deployment'
  params: {
    name: acrName
    location: location
    tags: tags
  }
}

// ─── PostgreSQL ───────────────────────────────────────────────
module postgres 'modules/postgres.bicep' = {
  scope: rg
  name: 'postgres-deployment'
  params: {
    name: '${baseName}-pg'
    location: location
    tags: tags
    administratorPassword: postgresAdminPassword
    databaseName: 'contentengine_${environment}'
  }
}

// ─── Redis ────────────────────────────────────────────────────
module redis 'modules/redis.bicep' = {
  scope: rg
  name: 'redis-deployment'
  params: {
    name: '${baseName}-redis'
    location: location
    tags: tags
  }
}

// ─── Storage ──────────────────────────────────────────────────
module storage 'modules/storage.bicep' = {
  scope: rg
  name: 'storage-deployment'
  params: {
    name: storageName
    location: location
    tags: tags
  }
}

// ─── AI Foundry (OpenAI) ──────────────────────────────────────
module foundry 'modules/foundry.bicep' = {
  scope: rg
  name: 'foundry-deployment'
  params: {
    name: '${baseName}-foundry'
    location: foundryLocation
    tags: tags
    deployments: [
      {
        name: 'gpt-4o'
        model: 'gpt-4o'
        version: '2024-08-06'
        capacity: 10
      }
      {
        name: 'gpt-4o-mini'
        model: 'gpt-4o-mini'
        version: '2024-07-18'
        capacity: 10
      }
    ]
  }
}

// ─── Container Apps Environment ───────────────────────────────
module cae 'modules/container-apps-env.bicep' = {
  scope: rg
  name: 'cae-deployment'
  params: {
    name: '${baseName}-cae'
    location: location
    tags: tags
  }
}

// ─── Key Vault ────────────────────────────────────────────────
module keyVault 'modules/key-vault.bicep' = {
  scope: rg
  name: 'kv-deployment'
  params: {
    name: '${baseName}-kv'
    location: location
    tags: tags
    managedIdentityPrincipalId: cae.outputs.managedIdentityPrincipalId
    databaseUrl: postgres.outputs.connectionString
    redisUrl: redis.outputs.connectionString
    blobStorageConnectionString: storage.outputs.connectionString
    foundryApiKey: foundry.outputs.apiKey
    foundryEndpoint: foundry.outputs.endpoint
  }
}

// ─── Worker Services (6x) — only deployed when images exist ───
var workerServices = [
  { name: 'template-service', image: 'template-service:latest' }
  { name: 'promotion-orchestrator', image: 'promotion-orchestrator:latest' }
  { name: 'scheduler', image: 'scheduler:latest' }
  { name: 'channel-worker', image: 'channel-worker:latest' }
  { name: 'activity-reporter', image: 'activity-reporter:latest' }
  { name: 'analytics-collector', image: 'analytics-collector:latest' }
]

module workers 'modules/container-app-service.bicep' = [
  for svc in workerServices: if (deployApps) {
    scope: rg
    name: '${svc.name}-deployment'
    params: {
      name: '${baseName}-${svc.name}'
      location: location
      tags: tags
      environmentId: cae.outputs.environmentId
      imageName: svc.image
      acrLoginServer: acr.outputs.loginServer
      acrPassword: acr.outputs.adminPassword
      acrUsername: acr.outputs.adminUsername
      managedIdentityId: cae.outputs.managedIdentityId
      managedIdentityClientId: cae.outputs.managedIdentityClientId
      keyVaultName: keyVault.outputs.vaultName
    }
  }
]

// ─── Management API ───────────────────────────────────────────
module api 'modules/container-app-api.bicep' = if (deployApps) {
  scope: rg
  name: 'management-api-deployment'
  params: {
    name: '${baseName}-management-api'
    location: location
    tags: tags
    environmentId: cae.outputs.environmentId
    imageName: 'management-api:latest'
    acrLoginServer: acr.outputs.loginServer
    acrPassword: acr.outputs.adminPassword
    acrUsername: acr.outputs.adminUsername
    managedIdentityId: cae.outputs.managedIdentityId
    managedIdentityClientId: cae.outputs.managedIdentityClientId
    keyVaultName: keyVault.outputs.vaultName
    corsAllowedOrigins: 'https://${baseName}-frontend.${cae.outputs.defaultDomain}'
    frontendUrl: 'https://${baseName}-frontend.${cae.outputs.defaultDomain}'
  }
}

// ─── Frontend ─────────────────────────────────────────────────
module frontend 'modules/container-app-frontend.bicep' = if (deployApps) {
  scope: rg
  name: 'frontend-deployment'
  params: {
    name: '${baseName}-frontend'
    location: location
    tags: tags
    environmentId: cae.outputs.environmentId
    imageName: 'frontend:latest'
    acrLoginServer: acr.outputs.loginServer
    acrPassword: acr.outputs.adminPassword
    acrUsername: acr.outputs.adminUsername
  }
}

// ─── Seed Worker Job ──────────────────────────────────────────
module seedJob 'modules/container-app-job.bicep' = if (deployApps) {
  scope: rg
  name: 'seed-worker-deployment'
  params: {
    name: '${baseName}-seed-worker'
    location: location
    tags: tags
    environmentId: cae.outputs.environmentId
    imageName: 'seed-worker:latest'
    acrLoginServer: acr.outputs.loginServer
    acrPassword: acr.outputs.adminPassword
    acrUsername: acr.outputs.adminUsername
    managedIdentityId: cae.outputs.managedIdentityId
    managedIdentityClientId: cae.outputs.managedIdentityClientId
    keyVaultName: keyVault.outputs.vaultName
  }
}

// ─── Outputs ──────────────────────────────────────────────────
output resourceGroupName string = rg.name
output acrLoginServer string = acr.outputs.loginServer
output managementApiUrl string = deployApps ? api.outputs.url : ''
output frontendUrl string = deployApps ? frontend.outputs.url : ''
output defaultDomain string = cae.outputs.defaultDomain
output keyVaultName string = keyVault.outputs.vaultName
output postgresFqdn string = postgres.outputs.fqdn
output foundryEndpoint string = foundry.outputs.endpoint
