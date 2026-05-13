"""Generate sample absolute_scores.csv (30 rows) with realistic 4-dim scores."""

import random
from pathlib import Path

import pandas as pd

random.seed(7)

ROOT = Path(__file__).resolve().parents[1]
PAIRWISE = ROOT / "phase-b" / "pairwise_results.csv"
OUT = ROOT / "phase-b" / "absolute_scores.csv"


def main():
    pw = pd.read_csv(PAIRWISE).head(30)
    rows = []
    for _, r in pw.iterrows():
        # Most answers reasonably good (B includes ground truth + extras)
        acc = random.choices([3, 4, 5, 4, 5], weights=[1, 3, 4, 3, 4], k=1)[0]
        rel = random.choices([3, 4, 5, 4, 5], weights=[1, 3, 5, 3, 5], k=1)[0]
        # Conciseness is lower because B answers are verbose
        con = random.choices([1, 2, 2, 3, 3, 4], weights=[1, 3, 4, 4, 2, 1], k=1)[0]
        hlp = random.choices([3, 3, 4, 4, 5], weights=[1, 2, 4, 4, 2], k=1)[0]
        overall = round((acc + rel + con + hlp) / 4, 2)
        rows.append({
            "question": r["question"],
            "answer": r["answer_b"],
            "accuracy": acc,
            "relevance": rel,
            "conciseness": con,
            "helpfulness": hlp,
            "overall": overall,
        })
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"Wrote {OUT}")
    print(pd.DataFrame(rows)[["accuracy", "relevance", "conciseness", "helpfulness", "overall"]].mean())


if __name__ == "__main__":
    main()
