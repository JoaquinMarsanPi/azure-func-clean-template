// Crea/actualiza un Azure Container App nativo de Functions (kind=functionapp)
// Reusa Environment, ACR y Storage existentes.

@description('Nombre del Container App (ej: func-clean-template)')
param containerAppName string

@description('Nombre del Container Apps Environment existente (ej: cae-ai-agentes-lab)')
param environmentName string

@description('Ubicación (default: la del RG)')
param location string = resourceGroup().location

@description('Imagen completa (ej: acraiagenteslab.azurecr.io/func-clean-template:0.1)')
param containerImage string

@description('Servidor del ACR (ej: acraiagenteslab.azurecr.io)')
param registryServer string

@secure()
@description('Connection string de Storage para Azure Functions (AzureWebJobsStorage)')
param storageConnectionString string

@description('Exponer endpoint público')
param ingressExternal bool = true

@description('Puerto interno del runtime (Functions en contenedor = 80)')
param targetPort int = 80

@description('Réplicas mínimas (0 = scale-to-zero)')
param minReplicas int = 0

@description('Réplicas máximas')
param maxReplicas int = 2

@description('vCPU (entero).')
param cpu int = 1

@description('Memoria (ej: 1Gi, 2Gi)')
param memory string = '2Gi'

@description('Usar identidad administrada para leer del ACR (system-assigned)')
param useRegistryIdentity bool = true

@description('Usuario del ACR (si useRegistryIdentity=false)')
param registryUsername string = ''

@secure()
@description('Password del ACR (si useRegistryIdentity=false)')
param registryPassword string = ''

// Environment existente
resource env 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: environmentName
}

// App (Functions nativo)
resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: containerAppName
  location: location
  kind: 'functionapp'

  identity: {
    type: 'SystemAssigned'
  }

  properties: {
    managedEnvironmentId: env.id

    configuration: {
      ingress: {
        external: ingressExternal
        targetPort: targetPort
      }

      // Secrets: storage (+ opcional password del ACR)
      secrets: useRegistryIdentity
        ? [
            {
              name: 'azurewebjobsstorage'
              value: storageConnectionString
            }
          ]
        : [
            {
              name: 'azurewebjobsstorage'
              value: storageConnectionString
            }
            {
              name: 'acr-pwd'
              value: registryPassword
            }
          ]

      // Registry: identidad o user/pass
      registries: useRegistryIdentity
        ? [
            {
              server: registryServer
              identity: 'system'
            }
          ]
        : [
            {
              server: registryServer
              username: registryUsername
              passwordSecretRef: 'acr-pwd'
            }
          ]
    }

    template: {
      containers: [
        {
          name: containerAppName
          image: containerImage
          resources: {
            cpu: cpu
            memory: memory
          }
          // <<-- ACÁ van las variables de entorno
          env: [
            {
              name: 'AzureWebJobsStorage'
              secretRef: 'azurewebjobsstorage'
            }
          ]
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

output fqdn string = app.properties.configuration.ingress.fqdn
