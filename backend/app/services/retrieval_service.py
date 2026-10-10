import math
import re
from typing import List, Dict, Any

class SimpleBM25Retriever:
    """
    Lightweight, modular local BM25/TF-IDF document chunk retriever.
    Can easily be swapped for FAISS/ChromaDB without breaking service interfaces.
    """
    @staticmethod
    def tokenize(text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())

    @classmethod
    def retrieve(cls, chunks: List[Dict[str, Any]], query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        query_tokens = cls.tokenize(query)
        if not query_tokens:
            return chunks[:top_k]

        scored_chunks = []
        doc_count = len(chunks)

        # Precompute document frequencies
        df = {}
        for chunk in chunks:
            tokens = set(cls.tokenize(chunk["content"]))
            for t in tokens:
                df[t] = df.get(t, 0) + 1

        for chunk in chunks:
            chunk_tokens = cls.tokenize(chunk["content"])
            score = 0.0
            for qt in query_tokens:
                if qt in chunk_tokens:
                    tf = chunk_tokens.count(qt)
                    idf = math.log((doc_count + 1) / (df.get(qt, 0) + 0.5))
                    score += tf * idf

            scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_chunks[:top_k]]