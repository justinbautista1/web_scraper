import os

from azure.storage.blob import ContainerClient
from dotenv import load_dotenv

load_dotenv()

container_client = ContainerClient.from_connection_string(
    conn_str=os.getenv("AZURE_STORAGE_CONN_STR"), container_name="internet-jury"
)

mds = []
blobs = container_client.list_blob_names()
for blob in blobs:
    blob_client = container_client.get_blob_client(blob)
    props = blob_client.get_blob_properties()
    md = {"name": props["name"], "metadata": props["metadata"]}
    mds.append(md)

print(mds)
