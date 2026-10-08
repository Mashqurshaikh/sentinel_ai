"""
Document text extraction.

Pulls plain text out of the file types employees actually paste into an AI
chat window as attachments - .txt, .pdf, .docx - so the same risk engine
that scans typed prompts can also scan uploaded files.
"""

import io
from pypdf import PdfReader
import docx


class UnsupportedFileType(Exception):
    pass


def extract_text(filename: str, file_bytes: bytes) -> str:
    name = filename.lower()

    if name.endswith(".txt") or name.endswith(".md") or name.endswith(".csv"):
        return file_bytes.decode("utf-8", errors="ignore")

    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if name.endswith(".docx"):
        document = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in document.paragraphs)

    raise UnsupportedFileType(f"Unsupported file type: {filename}. Supported: .txt, .md, .csv, .pdf, .docx")
