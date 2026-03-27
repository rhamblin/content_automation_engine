@description('Azure Container Registry for storing Docker images')
param name string
param location string
param tags object = {}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

@description('ACR login server (e.g. myacr.azurecr.io)')
output loginServer string = acr.properties.loginServer

@description('ACR admin username')
#disable-next-line outputs-should-not-contain-secrets
output adminUsername string = acr.listCredentials().username

@description('ACR admin password')
#disable-next-line outputs-should-not-contain-secrets
output adminPassword string = acr.listCredentials().passwords[0].value
