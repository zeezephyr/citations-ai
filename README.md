# Citations-ai
An early alpha designed to ingest archived web content and provide a simple user interface for querying it with ChatGPT.

# Getting started

## Setup

```
pip install -f requirements.txt
```

## Run the frontend

The frontend can be run either from the command line or with a web interface by passing in `-w`.

```
python app.py --help
usage: app.py [-h] [-q QUESTION] [-w] [-c COLLECTION] [-p DATA_PATH]

Ask OpenAI a question

options:
  -h, --help            show this help message and exit
  -q QUESTION, --question QUESTION
                        Specify a question to answer
  -w, --web             Start the web interface
  -c COLLECTION, --collection COLLECTION
                        The name of the vector collection
  -p DATA_PATH, --data-path DATA_PATH
                        The path to the ChromaDB directory
```

## Run the indexer

The indexer takes an archivebox data directory, scans it for htmltotext files, and then stores the embeddings for that data in a vector store so that `app.py` can leverage it when answering questions.

```
python indexer.py --help
usage: indexer.py [-h] [-d DIRECTORY] [-c COLLECTION] [-p DATA_PATH] [-a AFTER]

Scan an archivebox repository and store embeddings in chromadb

options:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        The path to the archivebox data repository
  -c COLLECTION, --collection COLLECTION
                        The name of the vector collection
  -p DATA_PATH, --data-path DATA_PATH
                        The path to persist the ChromaDB directory
  -a AFTER, --after AFTER
                        Only process files modified after this date
```