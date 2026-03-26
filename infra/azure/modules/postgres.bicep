@description('Azure Database for PostgreSQL Flexible Server')
param name string
param location string
param tags object = {}

@secure()
param administratorPassword string
param administratorLogin string = 'pgadmin'
param databaseName string = 'contentengine_dev'

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: administratorLogin
    administratorLoginPassword: administratorPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
  }
}

resource database 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: postgres
  name: databaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

// Allow Azure services to connect
resource firewallRule 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-12-01-preview' = {
  parent: postgres
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

@description('PostgreSQL connection string for application use')
#disable-next-line outputs-should-not-contain-secrets
output connectionString string = 'postgresql+asyncpg://${administratorLogin}:${administratorPassword}@${postgres.properties.fullyQualifiedDomainName}:5432/${databaseName}?ssl=require'

@description('PostgreSQL FQDN')
output fqdn string = postgres.properties.fullyQualifiedDomainName
