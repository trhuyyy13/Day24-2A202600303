"""Task B.1 — Pairwise Judge Pipeline với swap-and-average position bias mitigation.

So sánh 2 versions của RAG: baseline vs with re-ranker (hoặc current vs alt).

Usage:
    python phase-b/pairwise_judge.py

Output:
    phase-b/pairwise_results.csv (columns: question, answer_a, answer_b,
                                  run1_winner, run2_winner, winner_after_swap)
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
TESTSET = ROOT / "phase-a" / "testset_v1.csv"
RAG_RESULTS = ROOT / "phase-a" / "ragas_results.csv"
OUT = ROOT / "phase-b" / "pairwise_results.csv"

JUDGE_PROMPT_TMPL = """You are an impartial evaluator. Compare two answers to the same question.

Question: {question}
Answer A: {answer_a}
Answer B: {answer_b}

Rate based on:
- Factual accuracy
- Relevance to question
- Conciseness

Output JSON only:
{{"winner": "A" or "B" or "tie", "reason": "..."}}"""


def parse_judge_output(text: str) -> dict:
    """Robust JSON parsing với fallback."""
    try:
        cleaned = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Heuristic fallback: search for A/B/tie tokens
        lo = text.lower()
        if '"winner": "a"' in lo or "winner: a" in lo:
            return {"winner": "A", "reason": "Heuristic parse"}
        if '"winner": "b"' in lo or "winner: b" in lo:
            return {"winner": "B", "reason": "Heuristic parse"}
        return {"winner": "tie", "reason": "Parse error"}


def pairwise_judge_with_swap(question: str, ans_a: str, ans_b: str, judge_llm) -> dict:
    """Run judge 2 lần với order swap, aggregate to mitigate position bias."""
    # Run 1: A first
    prompt = JUDGE_PROMPT_TMPL.format(question=question, answer_a=ans_a, answer_b=ans_b)
    r1 = parse_judge_output(judge_llm.invoke(prompt).content)

    # Run 2: B first → flip winner back
    prompt2 = JUDGE_PROMPT_TMPL.format(question=question, answer_a=ans_b, answer_b=ans_a)
    r2 = parse_judge_output(judge_llm.invoke(prompt2).content)
    if r2.get("winner") == "A":
        r2["winner"] = "B"
    elif r2.get("winner") == "B":
        r2["winner"] = "A"

    # Aggregate
    if r1.get("winner") == r2.get("winner"):
        final = r1["winner"]
    else:
        final = "tie"

    return {
        "run1_winner": r1.get("winner", "tie"),
        "run2_winner": r2.get("winner", "tie"),
        "winner_after_swap": final,
        "run1_reason": r1.get("reason", "")[:200],
        "run2_reason": r2.get("reason", "")[:200],
    }


def get_two_rag_versions():
    """Return two callable versions of RAG to compare.

    Version A: baseline (top-3 retrieval, no rerank)
    Version B: with rerank (top-3 retrieval + cross-encoder rerank)
    """
    sys.path.insert(0, str(ROOT / "Day18-Track3-Production-RAG"))
    try:
        from src.pipeline import build_pipeline, run_query

        search, reranker = build_pipeline()

        def rag_a(q):  # no rerank
            r = search.search(q)
            ctx = [x.text for x in r[:3]]
            return ctx[0] if ctx else "Không tìm thấy."

        def rag_b(q):  # with rerank
            ans, _ = run_query(q, search, reranker)
            return ans

        return rag_a, rag_b
    except Exception as e:
        print(f"  Day 18 pipeline unavailable ({e}). Using mock A/B answers.")
        return _mock_versions()


def _mock_versions():
    """Mock answer generator: A gives shorter, B gives longer (for bias testing)."""
    df = pd.read_csv(RAG_RESULTS)
    answers_by_q = {r["question"]: r.get("ground_truth", "") for _, r in df.iterrows()}

    def rag_a(q):
        gt = answers_by_q.get(q, "Không có thông tin.")
        return gt.split(".")[0][:200] + "."

    def rag_b(q):
        gt = answers_by_q.get(q, "Không có thông tin.")
        return f"{gt} Bổ sung thêm: chi tiết liên quan thường được trình bày trong các văn bản hướng dẫn cụ thể, có hiệu lực thi hành theo quy định pháp luật."

    return rag_a, rag_b


def main(n_questions: int = 30):
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY chưa được set", file=sys.stderr)
        sys.exit(1)

    from langchain_openai import ChatOpenAI
    judge = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    print(f"[1/3] Loading {n_questions} questions...")
    df = pd.read_csv(TESTSET).head(n_questions)

    print("[2/3] Building two RAG versions...")
    rag_a, rag_b = get_two_rag_versions()

    print(f"[3/3] Judging {len(df)} pairs (each runs 2x for swap)...")
    rows = []
    start = time.time()
    for i, r in df.iterrows():
        q = r["question"]
        ans_a = rag_a(q)
        ans_b = rag_b(q)
        try:
            judged = pairwise_judge_with_swap(q, ans_a, ans_b, judge)
        except Exception as e:
            print(f"  Q{i+1} judge error: {e}")
            judged = {
                "run1_winner": "tie", "run2_winner": "tie",
                "winner_after_swap": "tie", "run1_reason": str(e)[:200], "run2_reason": "",
            }
        rows.append({
            "question": q,
            "answer_a": ans_a,
            "answer_b": ans_b,
            **judged,
        })
        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{len(df)}] {time.time()-start:.0f}s elapsed")

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(f"\nDone! {OUT}")
    print("\nWinner distribution (after swap):")
    print(out["winner_after_swap"].value_counts())


if __name__ == "__main__":
    main()
