@description('Azure Cache for Redis')
param name string
param location string
param tags object = {}

resource redis 'Microsoft.Cache/redis@2023-08-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: {}
  }
}

@description('Redis connection URL for application use (rediss:// for TLS)')
#disable-next-line outputs-should-not-contain-secrets
output connectionString string = 'rediss://:${redis.listKeys().primaryKey}@${redis.properties.hostName}:${redis.properties.sslPort}'

@description('Redis hostname')
output hostName string = redis.properties.hostName
