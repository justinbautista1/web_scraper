import os
from pathlib import Path

from azure.storage.blob import ContainerClient
from dotenv import load_dotenv

load_dotenv()

container_client = ContainerClient.from_connection_string(
    conn_str=os.getenv("AZURE_STORAGE_CONN_STR"), container_name="internet-jury"
)

dirname = "jury_service_intent"
directory = os.fsencode(dirname)
for file in os.listdir(directory):
    filename = f"ibm/{os.fsdecode(file)}"
    intent = filename.split(".")[0].split("/")[-1]

    metadata = {"source": "ibm", "intent": intent, "title": filename}

    blob_client = container_client.get_blob_client(filename)
    blob_path = Path(dirname) / os.fsdecode(file)
    with open(blob_path, "rb") as f:
        blob_client.upload_blob(f, metadata=metadata, overwrite=True)
