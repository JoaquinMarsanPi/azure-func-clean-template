# az_function_clean_architecture-
This is the Clean architeture for deploy in Azure Functions!
---

## Prerequisites

To run this Function App locally, ensure you have the following installed:

1. **Python** (version 3.8 or higher).
2. **Azure Functions Core Tools** ([installation guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)).
3. **Azure CLI** (optional for interacting with Azure resources).

### Create a Virtual Environment and Install Required Python Packages

1. Create a virtual environment:

    ```bash
    python -m venv .venv
    ```

2. Activate the virtual environment:

    - On Windows:
      ```bash
      .venv\Scripts\activate
      ```
    - On macOS/Linux:
      ```bash
      source .venv/bin/activate
      ```

3. Install the dependencies listed in `requirements.txt` using pip:

    ```bash
    pip install -r requirements.txt
    ```

---

## Running the Function Locally

1. Start the Azure Functions host locally:

    ```bash
    func start
    ```

2. Copy this local.setting.json:

    ```bash
    {
    "IsEncrypted": false,
    "Values": {
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "AzureWebJobsStorage": "UseDevelopmentStorage=true"
    }
}
    ```

3. Once started, the function's Event Grid trigger will be listening for events on the configured local endpoint, typically:

    ```
    [POST] http://localhost:7071/api/ping
    ```

---

## Testing the Function Locally

You can test the Event Grid trigger locally using the following steps:

1. **Simulate an Event Grid Trigger:** Use tools like `curl` or Postman to send a test HTTP POST request to the function's local endpoint. Example request:

    ```bash
    curl -X POST http://localhost:7071/api/ping \
        -H "Content-Type: application/json" 
    ```

2. **Inspect Logs:** Check the console output to ensure the event is processed correctly and logs reflect the expected behavior.

3. **Debugging:** If there are issues, ensure the database and email service configurations are accessible and verify the local settings in `local.settings.json`.

---

## Notes
- Make sure to update the `local.settings.json` file with the correct database and email service configuration.
- The classification logic and email forwarding are currently configured for development purposes and should be tested thoroughly before deployment.