import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import semchunk
import tiktoken


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

    def _token_counter(self, text):
        encoder = tiktoken.encoding_for_model("gpt-4")
        return len(encoder.encode(text))

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
            index_json = json.load(index_file)
            
            documents = semchunk.chunk(
                file.read_text(), chunk_size=256, token_counter=self._token_counter
            )
            ids = [f"{index_json["hash"]}-{i}" for (i, doc) in enumerate(documents)]
            metadata = [{"website": index_json["base_url"], 
                         "domain": index_json["domain"]} 
                         for doc in enumerate(documents)]

            yield ids, documents, metadata



class MarkdownScanner(LocalScanner):
    def __init__(self, scan_dir, config, metadata):
        super().__init__(scan_dir, config)
        self._metadata = metadata

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

            documents = semchunk.chunk(
                file.read_text(), chunk_size=256, token_counter=self._token_counter
            )
            ids = [f"{self.current_file}-{i}" for (i, doc) in enumerate(documents)]
            metadata = [self._metadata for doc in enumerate(documents)]

            yield ids, documents, metadata
