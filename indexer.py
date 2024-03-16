import argparse
import chromadb
import json
import os
import yaml

from chromadb.config import Settings
from datetime import datetime, timezone
from dotenv import load_dotenv
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

parser.add_argument("-q", "--query", type=str)

args = parser.parse_args()

client = chromadb.PersistentClient(path=args.data_path, settings=Settings(anonymized_telemetry=False))
collection = client.get_or_create_collection(name=args.collection)

pathlist = Path(args.directory).rglob("htmltotext.txt")
for file in pathlist:
    file_dir = os.path.dirname(file.resolve())
    index_file_path = os.path.join(file_dir, "index.json")
    index_modified_time = datetime.fromtimestamp(os.path.getmtime(index_file_path), tz=timezone.utc)

    if index_modified_time < args.after:
        continue

    index_file = open(index_file_path, "r")
    index = json.load(index_file)
    with file.open() as f:
        collection.upsert(
            ids=[index["hash"]],
            documents=[f.read()],
            metadatas=[{"website": index["base_url"], "domain": index["domain"]}]
        )

config['last_scan_time'] = START_TIME
with open(CONFIG_FILE_PATH, "a+") as config_file:
    yaml.safe_dump(config, config_file)
