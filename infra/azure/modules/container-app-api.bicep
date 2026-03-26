@description('Management API Container App with external ingress')
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

param corsAllowedOrigins string
param frontendUrl string
param azureEntraClientId string = ''

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
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        corsPolicy: {
          allowedOrigins: [corsAllowedOrigins]
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          allowCredentials: true
        }
      }
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
            cpu: json('0.5')
            memory: '1Gi'
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
            {
              name: 'CORS_ALLOWED_ORIGINS'
              value: corsAllowedOrigins
            }
            {
              name: 'FRONTEND_URL'
              value: frontendUrl
            }
            {
              name: 'AZURE_ENTRA_CLIENT_ID'
              value: azureEntraClientId
            }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

@description('Management API FQDN')
output fqdn string = app.properties.configuration.ingress.fqdn

@description('Management API URL')
output url string = 'https://${app.properties.configuration.ingress.fqdn}'
