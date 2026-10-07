"""Run the 20 test questions.

  python -m src.evaluate --retrieval-only   # no API key; measures retrieval + refusal threshold
  python -m src.evaluate                    # full run with Claude; writes results/python_run.csv

Automated columns are a first pass. Read the answers and confirm
'answer_correct' by hand before you quote any number.
"""
import argparse
import csv
import json
import re
from pathlib import Path

from dotenv import load_dotenv

from .agent import MIN_SCORE, answer, retrieve
from .retrieval import Retriever

ROOT = Path(__file__).resolve().parents[2]
QUESTIONS = ROOT / "test" / "test_questions.json"
RESULTS = ROOT / "results"


def parse_expected(tag: str) -> tuple[str, str]:
    doc, sec = tag.split(" s")
    return doc, sec


def retrieval_eval(questions, retriever, k=3):
    rows = []
    for q in questions:
        hits, relevant = retrieve(retriever, q["question"], k)
        got = {(c.doc_id, c.section_no) for c, _ in hits}
        got_docs = {d for d, _ in got}
        exp = [parse_expected(t) for t in q["expected_sources"]]
        exp_docs = {d for d, _ in exp}
        refused = not relevant
        rows.append({
            "id": q["id"], "category": q["category"], "should_refuse": q["should_refuse"],
            "top_score": round(hits[0][1], 3),
            "top3": " | ".join(f"{c.doc_id} s{c.section_no} ({s:.2f})" for c, s in hits),
            "section_hit": (not exp) or any(e in got for e in exp),
            "doc_hit": (not exp_docs) or bool(exp_docs & got_docs),
            "refused_by_threshold": refused,
            "refusal_correct": refused == q["should_refuse"],
        })
    return rows


def summarize_retrieval(rows):
    answerable = [r for r in rows if not r["should_refuse"]]
    oos = [r for r in rows if r["should_refuse"]]
    pct = lambda n, d: f"{100 * n / d:.0f}% ({n}/{d})" if d else "n/a"
    print(f"MIN_SCORE guard: {MIN_SCORE}")
    print("Right section in top-k (answerable): ", pct(sum(r["section_hit"] for r in answerable), len(answerable)))
    print("Right document in top-k (answerable):", pct(sum(r["doc_hit"] for r in answerable), len(answerable)))
    print("Answerable not wrongly refused:      ", pct(sum(not r["refused_by_threshold"] for r in answerable), len(answerable)))
    print("Out-of-scope caught by guard:        ", pct(sum(r["refused_by_threshold"] for r in oos), len(oos)))


def full_eval(questions, retriever):
    rows = []
    for q in questions:
        res = answer(q["question"], retriever)
        text = res["answer"]
        cited = set(re.findall(r"DOC-\d{2}", text))
        exp_docs = {parse_expected(t)[0] for t in q["expected_sources"]}
        source_ok = (not res["refused"] and exp_docs <= cited) if exp_docs else not cited
        keywords_ok = all(k.lower() in text.lower() for k in q["must_include"])
        rows.append({
            "id": q["id"], "category": q["category"], "question": q["question"],
            "answer": text.replace("\n", " / "), "refused": res["refused"],
            "refusal_correct": res["refused"] == q["should_refuse"],
            "source_correct_auto": source_ok, "keywords_present_auto": keywords_ok,
            "answer_correct_manual": "",  # <- you fill this in
        })
    return rows


def main():
    load_dotenv()
    ap = argparse.ArgumentParser()
    ap.add_argument("--retrieval-only", action="store_true")
    ap.add_argument("--k", type=int, default=3, help="chunks to retrieve")
    args = ap.parse_args()
    questions = json.loads(QUESTIONS.read_text())
    retriever = Retriever()
    RESULTS.mkdir(exist_ok=True)

    if args.retrieval_only:
        rows = retrieval_eval(questions, retriever, args.k)
        out = RESULTS / f"retrieval_eval_k{args.k}.csv"
    else:
        rows = full_eval(questions, retriever)  # uses k=3 (agent default)
        out = RESULTS / "python_run.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    if args.retrieval_only:
        summarize_retrieval(rows)
    else:
        print(f"Wrote {out}. Review answers and fill in answer_correct_manual.")


if __name__ == "__main__":
    main()
