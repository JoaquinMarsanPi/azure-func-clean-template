FROM mcr.microsoft.com/azure-functions/python:4-python3.10

ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

# deps primero (mejor cache)
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt

# código: en este template el code vive en la RAÍZ
COPY . /home/site/wwwroot/

EXPOSE 80
