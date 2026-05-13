"""Task B.2 — Absolute Scoring với Rubric.

Score answers theo 4 dimensions, 1-5 scale:
- accuracy
- relevance
- conciseness
- helpfulness

Overall = average of 4.

Usage:
    python phase-b/absolute_judge.py
"""

import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
PAIRWISE = ROOT / "phase-b" / "pairwise_results.csv"
TESTSET = ROOT / "phase-a" / "testset_v1.csv"
OUT = ROOT / "phase-b" / "absolute_scores.csv"

ABSOLUTE_PROMPT = """Score the answer on 4 dimensions, each 1-5 scale:

1. Accuracy (1=many errors, 5=fully accurate)
2. Relevance (1=off-topic, 5=directly answers)
3. Conciseness (1=verbose, 5=appropriately brief)
4. Helpfulness (1=unclear, 5=actionable)

Question: {question}
Answer: {answer}

Output JSON only:
{{"accuracy": int, "relevance": int, "conciseness": int, "helpfulness": int, "overall": float}}"""


def parse_json(text: str) -> dict:
    try:
        return json.loads(text.replace("```json", "").replace("```", "").strip())
    except json.JSONDecodeError:
        return {}


def absolute_score(question: str, answer: str, judge_llm) -> dict:
    prompt = ABSOLUTE_PROMPT.format(question=question, answer=answer)
    out = judge_llm.invoke(prompt).content
    parsed = parse_json(out)
    if not parsed:
        return {"accuracy": 3, "relevance": 3, "conciseness": 3, "helpfulness": 3, "overall": 3.0}

    dims = ["accuracy", "relevance", "conciseness", "helpfulness"]
    for d in dims:
        parsed.setdefault(d, 3)
    if "overall" not in parsed:
        parsed["overall"] = round(sum(parsed[d] for d in dims) / 4, 2)
    return parsed


def main(n: int = 30):
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY chưa được set", file=sys.stderr)
        sys.exit(1)

    from langchain_openai import ChatOpenAI
    judge = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Use pairwise's answer_b (the longer/better answer) for absolute scoring
    pw = pd.read_csv(PAIRWISE).head(n)

    rows = []
    start = time.time()
    for i, r in pw.iterrows():
        q = r["question"]
        a = r["answer_b"]
        try:
            s = absolute_score(q, a, judge)
        except Exception as e:
            print(f"  Q{i+1} error: {e}")
            s = {"accuracy": 3, "relevance": 3, "conciseness": 3, "helpfulness": 3, "overall": 3.0}
        rows.append({"question": q, "answer": a, **s})
        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{len(pw)}] {time.time()-start:.0f}s elapsed")

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"\nWrote {OUT}")
    print(out[["accuracy", "relevance", "conciseness", "helpfulness", "overall"]].describe())


if __name__ == "__main__":
    main()
