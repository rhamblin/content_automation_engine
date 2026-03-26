@description('Container App Job for seed-worker (manual trigger)')
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

resource job 'Microsoft.App/jobs@2024-03-01' = {
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
    environmentId: environmentId
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 600
      replicaRetryLimit: 1
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
          env: [
            {
              name: 'AZURE_CLIENT_ID'
              value: managedIdentityClientId
            }
            {
              name: 'AZURE_KEYVAULT_NAME'
              value: keyVaultName
            }
          ]
        }
      ]
    }
  }
}

@description('Job name')
output jobName string = job.name
