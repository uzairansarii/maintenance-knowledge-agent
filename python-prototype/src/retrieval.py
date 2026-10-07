"""Chunking and TF-IDF retrieval for the maintenance documents.

Each markdown document is split on '## ' headings, so every chunk is one
numbered section. That gives us a document name AND a section for citations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs" / "md"


@dataclass
class Chunk:
    doc_id: str       # e.g. "DOC-02"
    doc_title: str    # e.g. "Brake Inspection Procedure"
    section: str      # e.g. "2. Inspection interval"
    section_no: str   # e.g. "2"
    text: str

    @property
    def citation(self) -> str:
        return f"{self.doc_id} {self.doc_title}, section {self.section}"


def load_chunks(docs_dir: Path = DOCS_DIR) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.glob("DOC-*.md")):
        raw = path.read_text(encoding="utf-8")
        title_line = re.search(r"^# (DOC-\d+) (.+)$", raw, re.M)
        doc_id, doc_title = title_line.group(1), title_line.group(2).strip()
        for block in re.split(r"^## ", raw, flags=re.M)[1:]:
            heading, _, body = block.partition("\n")
            no = heading.split(".")[0].strip()
            chunks.append(Chunk(doc_id, doc_title, heading.strip(), no, body.strip()))
    return chunks


class Retriever:
    def __init__(self, chunks: list[Chunk] | None = None):
        self.chunks = chunks or load_chunks()
        # Prepend the doc title and heading so they also count as search terms.
        self._corpus = [f"{c.doc_title}. {c.section}. {c.text}" for c in self.chunks]
        self.vectorizer = TfidfVectorizer(
            lowercase=True, stop_words="english", ngram_range=(1, 2), sublinear_tf=True
        )
        self.matrix = self.vectorizer.fit_transform(self._corpus)

    def search(self, query: str, k: int = 3) -> list[tuple[Chunk, float]]:
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        top = scores.argsort()[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in top]
