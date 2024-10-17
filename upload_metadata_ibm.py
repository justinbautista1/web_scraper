import os

from azure.storage.blob import ContainerClient
from dotenv import load_dotenv

load_dotenv()

container_client = ContainerClient.from_connection_string(
    conn_str=os.getenv("AZURE_STORAGE_CONN_STR"), container_name="internet-jury"
)

dirname = "jury_service_intent"
directory = os.fsencode(dirname)
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    intent = filename.split(".")[0]

    metadata = {"source": "ibm", "intent": intent, "title": filename}

    blob_client = container_client.get_blob_client(filename)
    blob_client.set_blob_metadata(metadata)
