import argparse
import chromadb
import itertools
import os

from pathlib import Path
from chromadb.config import Settings

#after = #after a given datetime (time since last scan)

parser = argparse.ArgumentParser(description='Scan an archivebox repository and store embeddings in a vectorstore')
parser.add_argument('directory', type=str)
parser.add_argument('-c', '--collection', type=str, default='citations')
# parser.add_argument('-a', '--after', default=after)
args = parser.parse_args()

client = chromadb.Client(Settings(anonymized_telemetry=False))
collection = client.get_or_create_collection(name=args.collection)

pathlist = Path(args.directory).rglob('htmltotext.txt')
pathlist = list(itertools.islice(pathlist, 10)) #TODO: Remove. temporarily get the first 10
for file in pathlist:
    file_dir = os.path.dirname(file.resolve())
    index_file = os.path.join(file_dir, 'index.json')
    with file.open() as f:
        collection.add(
            documents=[f.read()],
            ids=[str(f)]
        )

results = collection.query(
    query_texts=['this is a test'],
    n_results=1
)

print(results)