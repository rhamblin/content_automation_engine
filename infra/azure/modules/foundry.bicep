@description('Azure AI Foundry (OpenAI) resource')
param name string
param location string
param tags object = {}

@description('Model deployments to create (name + model + version + capacity)')
param deployments array = []

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  tags: tags
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: name
    publicNetworkAccess: 'Enabled'
  }
}

@batchSize(1)
resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = [
  for dep in deployments: {
    parent: account
    name: dep.name
    sku: {
      name: dep.?skuName ?? 'GlobalStandard'
      capacity: dep.capacity
    }
    properties: {
      model: {
        format: 'OpenAI'
        name: dep.model
        version: dep.version
      }
    }
  }
]

@description('Foundry endpoint URL')
output endpoint string = account.properties.endpoint

@description('Foundry API key')
#disable-next-line outputs-should-not-contain-secrets
output apiKey string = account.listKeys().key1
