@description('Frontend Container App with external ingress')
param name string
param location string
param tags object = {}

param environmentId string
param imageName string
param acrLoginServer string
@secure()
param acrPassword string
param acrUsername string

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 80
        transport: 'auto'
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
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
    }
  }
}

@description('Frontend FQDN')
output fqdn string = app.properties.configuration.ingress.fqdn

@description('Frontend URL')
output url string = 'https://${app.properties.configuration.ingress.fqdn}'
