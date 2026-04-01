import os
from pathlib import Path
from datetime import datetime
from config import SUPPORTED_EXTENSIONS
from file_loader import load_file, build_preview
from db import up_insert_document


class Indexer:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback

    def _status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def iter_supported_files(self, root_dir):
        for current_root, _, files in os.walk(root_dir, followlinks=False):
            for name in files:
                path = Path(current_root) / name
                if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    yield path

    def index_directory(self, root_dir):
        total = 0
        indexed = 0
        failed = 0
        new_added = 0

        for path in self.iter_supported_files(root_dir):
                total += 1
                stat = path.stat()
                content = load_file(path)
                modified_at = datetime.utcfromtimestamp(stat.st_mtime).isoformat()
                doc = {
                    "path": str(path.resolve()),
                    "filename": path.name,
                    "extension": path.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "modified_at": modified_at,
                    "content": content,
                    "preview": build_preview(content),
                }

                inserted = up_insert_document(doc)
                indexed += 1
                if inserted:
                    new_added += 1


        summary = {
            "total_found": total,
            "indexed": indexed,
            "failed": failed,
            "new_added": new_added,
        }

        self._status(new_added)
        return summary