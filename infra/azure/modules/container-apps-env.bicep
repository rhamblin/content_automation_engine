@description('Container Apps Environment with Log Analytics')
param name string
param location string
param tags object = {}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${name}-logs'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${name}-identity'
  location: location
  tags: tags
}

resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

@description('Container Apps Environment ID')
output environmentId string = env.id

@description('Container Apps Environment default domain')
output defaultDomain string = env.properties.defaultDomain

@description('Managed Identity principal ID (for Key Vault access policy)')
output managedIdentityPrincipalId string = managedIdentity.properties.principalId

@description('Managed Identity ID (for Container App assignment)')
output managedIdentityId string = managedIdentity.id

@description('Managed Identity client ID')
output managedIdentityClientId string = managedIdentity.properties.clientId
