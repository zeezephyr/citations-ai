import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml
from chromadb import PersistentClient
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_community.vectorstores.chroma import Chroma
from xdg_base_dirs import xdg_data_home, xdg_state_home

from scanners import ArchiveBoxScanner, MarkdownScanner

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

parser.add_argument(
    "-c",
    "--collection",
    type=str,
    default="citations",
    help="The name of the vector collection",
)

data_path = os.path.join(xdg_data_home(), "citations-ai", "data")
parser.add_argument(
    "-p",
    "--data-path",
    type=str,
    default=data_path,
    help="The path to persist the ChromaDB directory",
)
parser.add_argument(
    "-a",
    "--after",
    type=lambda d: datetime.strptime(d, "%Y-%m-%d %H:%M:%S%z"),
    help="Only process files modified after this date",
)

args = parser.parse_args()

# TODO: After is currently applied globally. May want to reconsider.
if "last_scan_time" not in config:
    config["last_scan_time"] = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
if args.after is not None:
    config["last_scan_time"] = args["after"]

client = PersistentClient(
    path=args.data_path, settings=Settings(anonymized_telemetry=False)
)
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection(name=args.collection)

for entry in config["data_dirs"]:
    scanner = None
    if entry["type"] == "archivebox":
        scan_dir = Path(entry["directory"])
        scanner = ArchiveBoxScanner(scan_dir, config)
    if entry["type"] == "markdown":
        scan_dir = Path(entry["directory"])
        domain = entry["domain"]
        metadata = entry["metadata"]
        scanner = MarkdownScanner(scan_dir, config, metadata, domain)

    for documents, doc_ids in scanner.run():
        current_file = scanner.current_file
        try:
            print(f"Processing file {current_file}\n")
            collection.upsert(
                ids=doc_ids,
                metadatas=[d.metadata for d in documents],
                documents=[d.page_content for d in documents],
            )
        except Exception as e:
            print(f"Failed to process {current_file}\n", e)

config["last_scan_time"] = START_TIME
with open(CONFIG_FILE_PATH, "w+") as config_file:
    yaml.safe_dump(config, config_file)
    # TODO: Order files by modified date and save this after each file processed
    # TODO: Or, update last_scan_time on each file then try/except and store regardless
