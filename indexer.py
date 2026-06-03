import os
from pathlib import Path
from datetime import datetime
from config import SUPPORTED_EXTENSIONS
from processors import get_processor_for_path
from db import up_insert_document
import math
import time


class Indexer:
    def __init__(self, status_callback=None):
        self.status_callback = status_callback

    def _status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def compute_path_score(self, path: Path, stat):
        try:
            now = time.time()
            depth = len(path.parts)
            depth_score = max(0, 10 - depth)

            ext = path.suffix.lower()
            ext_score = 0
            if ext == ".txt":
                ext_score = 3.0
            elif ext == ".docx":
                ext_score = 1.0

            
            recency_score = 0.0
            try:
                if stat.st_mtime is not None:
                    age = max(0.0, now - stat.st_mtime)
                    recency_window = 30 * 24 * 60 * 60
                    recency_score = max(0.0, 1.0 - (age / recency_window)) * 3.0
            except Exception:
                recency_score = 0.0

            
            size_score = 0.0
            try:
                size_score = min(5.0, math.log10(max(1, stat.st_size))) * 0.5
            except Exception:
                size_score = 0.0

            score = depth_score + ext_score + recency_score + size_score
            return float(score)
        except Exception:
            return 0.0

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
                processor = get_processor_for_path(path)
                processed = processor.process(path)
                modified_at = datetime.utcfromtimestamp(stat.st_mtime).isoformat()
                doc = {
                    "path": str(path.resolve()),
                    "filename": path.name,
                    "extension": path.suffix.lower(),
                    "size_bytes": stat.st_size,
                    "modified_at": modified_at,
                    "content": processed.get("content", ""),
                    "preview": processed.get("preview", ""),
                    "dominant_color": processed.get("dominant_color"),
                    "path_score": self.compute_path_score(path, stat),
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
