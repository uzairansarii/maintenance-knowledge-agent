"""Retrieval-grounded answering: top-k TF-IDF chunks -> Claude -> cited answer."""
from __future__ import annotations

import os

from .retrieval import Retriever

REFUSAL = "I don't have that information in the maintenance documents."

# Guard only: if NO chunk shares meaningful words with the question, refuse
# without calling the model. TF-IDF scores cannot separate out-of-scope
# questions from real ones (see README, "What I learned"), so the real refusal
# decision is made by the model under the grounding rule in SYSTEM_PROMPT.
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.05"))

SYSTEM_PROMPT = f"""You are a maintenance assistant for garage staff (mechanics and drivers).

RULES
1. Answer ONLY from the DOCUMENT EXCERPTS in the user message. Never use outside knowledge and never guess numbers.
2. Always cite the source after the answer in this form: Source: DOC-02 Brake Inspection Procedure, section 2.
3. If the excerpts do not answer the question, reply with exactly: {REFUSAL}
   Do not add a guess or a source in that case.
4. If the question is too vague to answer, ask ONE short clarifying question.
5. For safety-critical steps (brakes, tires, hydraulics, lifting, batteries), end with: Confirm with your supervisor before you proceed.
6. Style: plain language, short numbered steps, no long paragraphs."""


def build_user_message(question: str, hits) -> str:
    excerpts = "\n\n".join(
        f"[{c.doc_id} {c.doc_title}, section {c.section}]\n{c.text}" for c, _ in hits
    )
    return f"DOCUMENT EXCERPTS\n{excerpts}\n\nQUESTION\n{question}"


def retrieve(retriever: Retriever, question: str, k: int = 3):
    hits = retriever.search(question, k=k)
    relevant = [(c, s) for c, s in hits if s >= MIN_SCORE]
    return hits, relevant


def answer(question: str, retriever: Retriever | None = None, k: int = 3, model: str | None = None) -> dict:
    """Returns {answer, refused, hits}. Needs ANTHROPIC_API_KEY."""
    retriever = retriever or Retriever()
    hits, relevant = retrieve(retriever, question, k)
    if not relevant:  # nothing passed the threshold: refuse without calling the model
        return {"answer": REFUSAL, "refused": True, "hits": hits}

    import anthropic  # imported here so retrieval-only runs need no API key

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model or os.getenv("MODEL", "claude-haiku-4-5-20251001"),
        max_tokens=600,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_message(question, relevant)}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    return {"answer": text, "refused": text.startswith("I don't have that information"), "hits": hits}
