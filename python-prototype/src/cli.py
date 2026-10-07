"""Interactive chat:  python -m src.cli   (add --retrieve-only to skip the API)"""
import argparse

from dotenv import load_dotenv

from .agent import answer, retrieve
from .retrieval import Retriever


def main():
    load_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--retrieve-only", action="store_true", help="show retrieved chunks, no API call")
    args = p.parse_args()
    r = Retriever()
    print("Maintenance assistant (Python prototype). Ctrl+C to quit.\n")
    while True:
        try:
            q = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not q:
            continue
        if args.retrieve_only:
            for c, s in retrieve(r, q)[0]:
                print(f"  {s:.2f}  {c.citation}")
        else:
            res = answer(q, r)
            print(f"\nAssistant: {res['answer']}\n")


if __name__ == "__main__":
    main()
