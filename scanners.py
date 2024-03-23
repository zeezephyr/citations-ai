import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import (
    MarkdownTextSplitter,
    SentenceTransformersTokenTextSplitter,
)


class LocalScanner(ABC):
    def __init__(self, scan_dir: Path, config: dict):
        self._scan_dir = scan_dir
        self._config = config

    @abstractmethod
    def _list_files(self):
        pass

    def _preprocess_files(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @property
    def current_file(self):
        return self._current_file


class ArchiveBoxScanner(LocalScanner):
    def __init__(self, scan_dir, config):
        super().__init__(scan_dir, config)

    def _list_files(self):
        return self._scan_dir.rglob("htmltotext.txt")

    def run(self):
        pathlist = self._list_files()
        for file in pathlist:
            self._current_file = file
            file_dir = os.path.dirname(file.resolve())
            index_file_path = os.path.join(file_dir, "index.json")
            index_modified_time = datetime.fromtimestamp(
                os.path.getmtime(index_file_path), tz=timezone.utc
            )

            if index_modified_time < self._config["last_scan_time"]:
                continue

            index_file = open(index_file_path, "r")
            index = json.load(index_file)

            raw_documents = TextLoader(str(file)).load()
            text_splitter = SentenceTransformersTokenTextSplitter(
                chunk_overlap=50, model_name="all-MiniLM-L6-v2"
            )
            documents = text_splitter.split_documents(raw_documents)

            for d in documents:
                d.metadata["website"] = index["base_url"]
                d.metadata["domain"] = index["domain"]

            yield documents


class MarkdownScanner(LocalScanner):
    def __init__(self, scan_dir, config, metadata: str = None, domain: str = None):
        super().__init__(scan_dir, config)
        self._metadata = metadata
        self._domain = domain

    def _list_files(self):
        return self._scan_dir.rglob("*.md")

    def run(self):
        pathlist = self._list_files()
        for file in pathlist:
            self._current_file = file
            file_modified_time = datetime.fromtimestamp(
                os.path.getmtime(file), tz=timezone.utc
            )

            if file_modified_time < self._config["last_scan_time"]:
                continue

            raw_documents = TextLoader(str(file)).load()
            text_splitter = MarkdownTextSplitter()
            documents = text_splitter.split_documents(raw_documents)

            for d in documents:
                if self._domain is not None:
                    d.metadata["domain"] = self._domain
                if self._metadata is not None:
                    d.metadata["source"] = self._metadata

            yield documents
