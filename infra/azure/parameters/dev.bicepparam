using '../main.bicep'

param environment = 'dev'
param location = 'canadacentral'
param projectName = 'content-engine'

param foundryLocation = 'eastus2'

// Provide at deploy time via: --parameters postgresAdminPassword=<value>
param postgresAdminPassword = ''
