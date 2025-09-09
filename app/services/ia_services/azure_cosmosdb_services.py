from azure.cosmos import cosmos_client, exceptions, http_constants, PartitionKey

from app.core.config import (
    AZURE_DB_ENDPOINT,
    AZURE_DB_KEY,
    AZURE_DB_CONTAINER_NAME,
    AZURE_DB_DATABASE_NAME
)


class CosmosDB:

    def __init__(self, container:str=AZURE_DB_CONTAINER_NAME):
        self.client = cosmos_client.CosmosClient(AZURE_DB_ENDPOINT, {'masterKey': AZURE_DB_KEY})
        self.database = self.get_database(AZURE_DB_DATABASE_NAME)
        self.container = self.get_container(container)

    def get_database(self, database_name):
        try:
            return self.client.get_database_client(database_name)
        except exceptions.CosmosResourceExistsError:
            print(f"Database '{database_name}' created successfully.")
            return self.client.create_database_if_not_exists(id=database_name)

    def get_container(self, container_name):
        # Create a container
        try:
            return self.database.get_container_client(container_name)
        except exceptions.CosmosResourceExistsError:
            print(f"Container '{container_name}' created successfully.")
            return self.database.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path="/id"),
                offer_throughput=400
            )

    def insert(self, row):
        try:
            self.container.create_item(body=row)
            print("Item created successfully.")
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == http_constants.StatusCodes.CONFLICT:
                print("Item already exists.")
            else:
                raise

    def read_item(self, id):
        try:
            response = self.container.read_item(item=id, partition_key=id)
            return response
        except Exception as e:
            print(f"Item not found id: {id}. Error {str(e)}")
            return None

    def update_item(self, item):
        try:
            self.container.upsert_item(body=item)
            # print("Item updated successfully.")
        except Exception as e:
            print(f"Item not found for update. {str(e)}")
            print(f"value: {item}")

    def delete_item(self, id):
        try:
            self.container.delete_item(item=id, partition_key=id)
            print("Item deleted successfully.")
        except exceptions.CosmosHttpResponseError as e:
            if e.status_code == http_constants.StatusCodes.NOT_FOUND:
                print("Item not found for deletion.")
            else:
                raise
