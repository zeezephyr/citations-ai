import argparse
import json
import os
import yaml

from chromadb.config import Settings
from chromadb import PersistentClient
from datetime import datetime, timezone
from dotenv import load_dotenv
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings
)
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_text_splitters import SentenceTransformersTokenTextSplitter
from pathlib import Path
from xdg_base_dirs import xdg_data_home, xdg_state_home

START_TIME = datetime.now(tz=timezone.utc)

load_dotenv()
CONFIG_FILE_PATH = os.path.join(xdg_state_home(), "citations-ai", "config.yaml")
os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)

with open(CONFIG_FILE_PATH, "a") as file:
    pass

with open(CONFIG_FILE_PATH, "r+") as config_file:
    config = yaml.safe_load(config_file)
    if config is None:
        config = {}

parser = argparse.ArgumentParser(
    description="Scan an archivebox repository and store embeddings in chromadb"
)
parser.add_argument("directory", type=str)
parser.add_argument("-c", "--collection", type=str, default="citations")

data_path = os.path.join(xdg_data_home(), "citations-ai", "data")
parser.add_argument("-d", "--data-path", type=str, default=data_path)

if "last_scan_time" in config:
    after = config['last_scan_time']
else:
    after = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
parser.add_argument("-a", "--after", default=after)

args = parser.parse_args()

client = PersistentClient(path=args.data_path, settings=Settings(anonymized_telemetry=False))
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection(name=args.collection)

vectorstore = Chroma(
    client=client,
    collection_name=args.collection,
    embedding_function=embedding_function
)

pathlist = Path(args.directory).rglob("htmltotext.txt")
for file in pathlist:
    file_dir = os.path.dirname(file.resolve())
    index_file_path = os.path.join(file_dir, "index.json")
    index_modified_time = datetime.fromtimestamp(os.path.getmtime(index_file_path), tz=timezone.utc)

    if index_modified_time < args.after:
        continue

    index_file = open(index_file_path, "r")
    index = json.load(index_file)

    print(f'Processing {file}')
    raw_documents = TextLoader(str(file)).load()
    text_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=50, model_name="all-MiniLM-L6-v2")
    documents = text_splitter.split_documents(raw_documents)

    for d in documents:
        d.metadata['website'] = index['base_url']
        d.metadata['domain'] = index['domain']

    try:
        vectorstore.add_documents(documents)
    except Exception as e:
        print(f'Failed to process {file}\n', e)

config['last_scan_time'] = START_TIME
with open(CONFIG_FILE_PATH, "a+") as config_file:
    yaml.safe_dump(config, config_file) # TODO: Order files by modified date and save this after each file processed
