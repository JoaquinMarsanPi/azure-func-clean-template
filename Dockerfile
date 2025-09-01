FROM mcr.microsoft.com/azure-functions/python:4-python3.10
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true
COPY ./src /home/site/wwwroot
RUN python -m pip install --no-cache-dir -r /home/site/wwwroot/requirements.txt
EXPOSE 80