targetScope = 'resourceGroup'

// Nombres básicos (podés dejarlos así o sobreescribir con -p)
@description('Nombre del ACR')
param acrName string = 'acraiagenteslab'
@description('Nombre del Container Apps Environment')
param envName string = 'cae-ai-agentes-lab'
@description('Nombre del Log Analytics')
param workspaceName string = 'law-ai-agentes-lab'
@description('Nombre del Storage (si no lo pasás, se genera)')
param storageName string = toLower('st' + uniqueString(resourceGroup().id))
@description('Nombre del Container App')
param containerAppName string = 'func-clean-template'

@description('Región')
param location string = resourceGroup().location

// Imagen a usar: <loginServer>/<repo>:<tag> (ej: acraiagenteslab.azurecr.io/func-clean-template:0.1)
// Para el 1er despliegue podés crear solo la infra (deployContainerApp=false) y luego volver a correr con true.
@description('Nombre de la imagen (repo:tag)')
param imageName string = 'func-clean-template:0.1'

// Tamaño y escala
@description('vCPU (0.25/0.5/1/2/3/4)')
param cpu number = 0.5
@description('Memoria (1Gi/2Gi/...)')
param memory string = '1Gi'
@description('Mínimo de réplicas (0=scale-to-zero)')
param minReplicas int = 0
@description('Máximo de réplicas')
param maxReplicas int = 2

// Crear el Container App en este despliegue (si false, crea solo la infra)
@description('Crear el Container App en este despliegue')
param deployContainerApp bool = true

// ACR
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: false
  }
}
var registryServer = '${acr.name}.azurecr.io'

// Log Analytics
resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: workspaceName
  location: location
  properties: {
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}
var lawKeys = listKeys(law.id, '2020-08-01')

// Container Apps Environment (con logs a Log Analytics)
resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: lawKeys.primarySharedKey
      }
    }
  }
}

// Storage (para AzureWebJobsStorage)
resource st 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
  }
}
var stKeys = listKeys(st.id, '2023-01-01')
var storageConn = 'DefaultEndpointsProtocol=https;AccountName=${st.name};AccountKey=${stKeys.keys[0].value};EndpointSuffix=${environment().suffixes.storage}'

// Container App (Functions nativo)
resource app 'Microsoft.App/containerApps@2024-03-01' = if (deployContainerApp) {
  name: containerAppName
  location: location
  kind: 'functionapp'
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 80
      }
      secrets: [
        { name: 'azurewebjobsstorage', value: storageConn }
      ]
      registries: [
        { server: registryServer, identity: 'system' }
      ]
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: '${registryServer}/${imageName}'
          resources: { cpu: cpu, memory: memory }
          env: [
            { name: 'AzureWebJobsStorage', secretRef: 'azurewebjobsstorage' }
          ]
        }
      ]
      scale: { minReplicas: minReplicas, maxReplicas: maxReplicas }
    }
  }
}

// Role assignment: dar ACR Pull a la identidad del Container App
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployContainerApp) {
  name: guid(acr.id, app.id, 'AcrPull')
  scope: acr
  properties: {
    principalId: app.identity.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalType: 'ServicePrincipal'
  }
}

output loginServer string = registryServer
output storageAccount string = st.name
output environmentName string = env.name
output containerApp string = deployContainerApp ? app.name : 'not-created'
output fqdn string = deployContainerApp ? app.properties.configuration.ingress.fqdn : 'not-created'
