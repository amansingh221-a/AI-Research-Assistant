import fitz  # PyMuPDF
from pathlib import Path
import uuid
import re
from typing import List, Dict, Tuple

class PDFProcessor:
    @staticmethod
    def extract_and_chunk(file_path: Path, chunk_size: int = 800, overlap: int = 150) -> Tuple[List[Dict], int, bool]:
        """
        Extracts page-by-page text from a PDF, detects if scanned, and produces overlapping chunks.
        """
        doc = fitz.open(file_path)
        page_count = len(doc)
        total_chars = 0
        pages_text: List[Tuple[int, str]] = []

        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text("text")
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            total_chars += len(cleaned_text)
            pages_text.append((page_num + 1, cleaned_text))

        doc.close()

        # Scanned PDF Detection heuristic (< 100 characters average per page)
        avg_chars = total_chars / max(page_count, 1)
        is_scanned = avg_chars < 100

        chunks: List[Dict] = []
        if is_scanned:
            return chunks, page_count, True

        for page_num, p_text in pages_text:
            if not p_text:
                continue
            words = p_text.split(" ")
            if len(words) <= chunk_size:
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "chunk_index": len(chunks),
                    "page_number": page_num,
                    "content": p_text,
                    "token_estimate": int(len(words) * 1.3)
                })
            else:
                step = chunk_size - overlap
                for i in range(0, len(words), step):
                    chunk_words = words[i:i + chunk_size]
                    chunk_str = " ".join(chunk_words)
                    chunks.append({
                        "id": str(uuid.uuid4()),
                        "chunk_index": len(chunks),
                        "page_number": page_num,
                        "content": chunk_str,
                        "token_estimate": int(len(chunk_words) * 1.3)
                    })
                    if i + chunk_size >= len(words):
                        break

        return chunks, page_count, False