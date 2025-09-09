import os
import base64
from azure.storage.blob import BlobServiceClient


class StorageAccount:
    def __init__(self, connection_string, container_name):
        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)

    def download_blob(self, file_name):
        blob_client = self.container_client.get_blob_client(file_name)
        content = blob_client.download_blob().readall()
        return content

    def get_files_list(self, filter_name, download_folder=None):
        blobs = self.container_client.list_blobs(name_starts_with=filter_name)

        if download_folder is None:
            download_folder = "/tmp/"

        file_list = []

        for blob in blobs:
            blob_client = self.container_client.get_blob_client(blob)
            download_file_path = os.path.join(download_folder, blob.name)

            if not blob.name.endswith('.txt'):
                continue

            os.makedirs(os.path.dirname(download_file_path), exist_ok=True)

            with open(download_file_path, 'wb') as download_file:
                download_file.write(blob_client.download_blob().readall())
                file_list.append(download_file_path)

        return file_list
    
    def get_files_strings(self, filter_name):
        blobs = self.container_client.list_blobs(name_starts_with=filter_name)

        file_list = []
        for blob in blobs:
            blob_content = self.download_blob(blob.name)
            encoded_content = base64.b64encode(blob_content).decode('utf-8')
            file_list.append({
                'file_name': blob.name,
                'content_base64': encoded_content
            })

        return file_list
    
    def get_data_csv(self, blob, download_folder=None):

        if download_folder is None:
            download_folder = "/tmp/"

        blob_client = self.container_client.get_blob_client(blob)
        download_file_path = os.path.join(download_folder, blob)
        os.makedirs(os.path.dirname(download_file_path), exist_ok=True)

      
        with open(download_file_path, "wb") as download_file:
            blob_data = blob_client.download_blob()
            download_file.write(blob_data.readall())

            download_file.write(blob_client.download_blob().readall())

        return download_file_path
