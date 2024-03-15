import argparse
import chromadb
import itertools
import json
import os

from pathlib import Path
from chromadb.config import Settings
from xdg_base_dirs import xdg_data_home

# after = #after a given datetime (time since last scan)

parser = argparse.ArgumentParser(
    description="Scan an archivebox repository and store embeddings in chromadb"
)
parser.add_argument("directory", type=str)
parser.add_argument("-c", "--collection", type=str, default="citations")
data_path = os.path.join(xdg_data_home(), "citations-ai", "data")
parser.add_argument("-p", "--persist-data", type=str, default=data_path)
# parser.add_argument('-a', '--after', default=after)
args = parser.parse_args()

client = chromadb.PersistentClient(path=data_path, settings=Settings(anonymized_telemetry=False))
collection = client.get_or_create_collection(name=args.collection)

pathlist = Path(args.directory).rglob("htmltotext.txt")
pathlist = list(
    itertools.islice(pathlist, 10)
)  # TODO: Remove. temporarily get the first 10
for file in pathlist:
    file_dir = os.path.dirname(file.resolve())
    index_file = open(os.path.join(file_dir, "index.json"), "r")
    index = json.load(index_file)
    with file.open() as f:
        collection.upsert(
            ids=[index["hash"]],
            documents=[f.read()],
            metadatas=[{"website": index["base_url"], "domain": index["domain"]}]
        )

results = collection.query(query_texts=["this is a test"], n_results=1)
