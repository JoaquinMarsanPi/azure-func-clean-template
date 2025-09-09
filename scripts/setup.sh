#!/bin/bash

# Personaliza estas variables
RESOURCE_GROUP="pi-rg-dev-lab-acuello"
LOCATION="eastus"
STORAGE_ACCOUNT="storage$(openssl rand -hex 3 | tr -d '[:upper:]')"
FUNCTION_APP_NAME="func$(openssl rand -hex 3)"
RUNTIME="python"
PYTHON_VERSION="3.10"

# Crear Storage Account (obligatoria para la Function App)
az storage account create \
  --name $STORAGE_ACCOUNT \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --sku Standard_LRS

# Crear la Function App (consumption plan, Linux, Python 3.10)
az functionapp create \
  --name $FUNCTION_APP_NAME \
  --storage-account $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime $RUNTIME \
  --runtime-version $PYTHON_VERSION \
  --os-type Linux

echo "✅ Azure Function creada: https://$FUNCTION_APP_NAME.azurewebsites.net"
