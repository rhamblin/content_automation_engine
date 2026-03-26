@description('Reusable Container App module for internal worker services (no ingress)')
param name string
param location string
param tags object = {}

param environmentId string
param imageName string
param acrLoginServer string
@secure()
param acrPassword string
param acrUsername string

param managedIdentityId string
param managedIdentityClientId string
param keyVaultName string

param envVars array = []

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: acrLoginServer
          username: acrUsername
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        {
          name: 'acr-password'
          value: acrPassword
        }
      ]
    }
    template: {
      containers: [
        {
          name: name
          image: '${acrLoginServer}/${imageName}'
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: concat([
            {
              name: 'AZURE_CLIENT_ID'
              value: managedIdentityClientId
            }
            {
              name: 'AZURE_KEYVAULT_NAME'
              value: keyVaultName
            }
          ], envVars)
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

@description('Container App name')
output appName string = app.name
