from pathlib import Path
from docx import Document
from config import PREVIEW_MAX_CHARS


def read_txt(path: Path):
    return path.read_text(encoding="utf-8", errors="ignore")


def read_docx(path: Path):
    doc = Document(path)
    parts = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def load_file(path: Path):
    ext = path.suffix.lower()
    if ext == ".txt":
        return read_txt(path)
    if ext == ".docx":
        return read_docx(path)
    raise ValueError(f"Unsupported file type: {ext}")

def build_preview(content: str) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    preview = "\n".join(lines[:3])
    if not preview:
        preview = content[:PREVIEW_MAX_CHARS]
    return preview[:PREVIEW_MAX_CHARS]