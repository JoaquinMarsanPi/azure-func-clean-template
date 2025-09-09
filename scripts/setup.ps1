# Personaliza estas variables
$resourceGroup = "mi-grupo"
$location = "eastus"
$storageAccount = "storage" + -join ((1..6) | ForEach-Object { [char[]](48..57 + 97..122) | Get-Random })  # minúsculas
$functionAppName = "func" + -join ((1..6) | ForEach-Object { [char[]](48..57 + 97..122) | Get-Random })
$runtime = "python"
$pythonVersion = "3.10"

# Crear Storage Account
az storage account create `
  --name $storageAccount `
  --location $location `
  --resource-group $resourceGroup `
  --sku Standard_LRS

# Crear Function App
az functionapp create `
  --name $functionAppName `
  --storage-account $storageAccount `
  --resource-group $resourceGroup `
  --consumption-plan-location $location `
  --runtime $runtime `
  --runtime-version $pythonVersion `
  --os-type Linux

Write-Host "`n✅ Azure Function creada: https://$functionAppName.azurewebsites.net"
