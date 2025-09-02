targetScope = 'resourceGroup'

// ----------- Parámetros (podés dejar defaults) ------------
@description('Nombre del ACR')
param acrName string = 'acraiagenteslab'

@description('Nombre del Container Apps Environment')
param envName string = 'cae-ai-agentes-lab'

@description('Nombre del Log Analytics')
param workspaceName string = 'law-ai-agentes-lab'

@description('Nombre del Storage (si no pasás uno, se genera)')
param storageName string = toLower('st${uniqueString(resourceGroup().id)}')

@description('Nombre del Container App')
param containerAppName string = 'func-clean-template'

@description('Región')
param location string = resourceGroup().location

@description('Nombre de la imagen (repo:tag). Ej: func-clean-template:0.1')
param imageName string = 'func-clean-template:0.1'

@description('vCPU como string: 0.25/0.5/1/2/3/4')
param cpu string = '0.5'

@description('Memoria: 0.5Gi/1Gi/2Gi/...')
param memory string = '1Gi'

@description('Mínimo de réplicas (0=scale-to-zero)')
param minReplicas int = 0

@description('Máximo de réplicas')
param maxReplicas int = 2

@description('¿Crear también el Container App en este despliegue?')
param deployContainerApp bool = true

@description('Usar credenciales admin del ACR (true) o identidad administrada + AcrPull (false)')
param useAcrAdminCreds bool = true

// ---------------- ACR ----------------
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: { name: 'Basic' }
  properties: {
    adminUserEnabled: useAcrAdminCreds
  }
}
var registryServer = '${acr.name}.azurecr.io'
var acrCreds = useAcrAdminCreds ? listCredentials(acr.id, '2019-05-01') : null

// ------------- Log Analytics ----------
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
var lawShared = listKeys(law.id, '2020-08-01')

// --------- Container Apps Environment -
resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: lawShared.primarySharedKey
      }
    }
  }
}

// ---------------- Storage -------------
resource st 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
  }
}
var stKey = st.listKeys().keys[0].value
var storageConn = 'DefaultEndpointsProtocol=https;AccountName=${st.name};AccountKey=${stKey};EndpointSuffix=${environment().suffixes.storage}'

// ------------- Container App (Functions nativo) -------------
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
      secrets: useAcrAdminCreds
        ? [
            { name: 'azurewebjobsstorage', value: storageConn }
            { name: 'acr-pwd', value: acrCreds.passwords[0].value }
          ]
        : [
            { name: 'azurewebjobsstorage', value: storageConn }
          ]
      registries: useAcrAdminCreds
        ? [
            {
              server: registryServer
              username: acrCreds.username
              passwordSecretRef: 'acr-pwd'
            }
          ]
        : [
            { server: registryServer, identity: 'system' }
          ]
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: '${registryServer}/${imageName}'
          resources: { cpu: json(cpu), memory: memory }
          env: [
            { name: 'AzureWebJobsStorage', secretRef: 'azurewebjobsstorage' }
          ]
        }
      ]
      scale: { minReplicas: minReplicas, maxReplicas: maxReplicas }
    }
  }
}

// Si usás identidad administrada, damos permiso AcrPull
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (deployContainerApp && !useAcrAdminCreds) {
  name: guid(acr.id, app.id, 'AcrPull')
  scope: acr
  properties: {
    principalId: app.identity.principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalType: 'ServicePrincipal'
  }
}

// -------------------- Salidas --------------------
output loginServer string = registryServer
output storageAccount string = st.name
output environmentName string = env.name
output containerApp string = deployContainerApp ? app.name : 'not-created'
output fqdn string = deployContainerApp ? app.properties.configuration.ingress.fqdn : 'not-created'
