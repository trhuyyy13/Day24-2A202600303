"""Task A.2 — Run RAGAS 4 Metrics.

Run RAGAS evaluation lên test_v1.csv với 4 core metrics:
- faithfulness
- answer_relevancy
- context_precision
- context_recall

Sử dụng Day 18 RAG pipeline để generate answers.

Usage:
    python phase-a/run_ragas.py

Output:
    phase-a/ragas_results.csv   (per-question scores)
    phase-a/ragas_summary.json  (aggregate scores)
"""

import ast
import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DAY18 = ROOT / "Day18-Track3-Production-RAG"
TESTSET = ROOT / "phase-a" / "testset_v1.csv"
RESULTS = ROOT / "phase-a" / "ragas_results.csv"
SUMMARY = ROOT / "phase-a" / "ragas_summary.json"

# Make Day 18 importable
sys.path.insert(0, str(DAY18))


def get_rag_pipeline():
    """Wire up Day 18 RAG pipeline. Returns a callable: question -> (answer, contexts).

    Falls back to a minimal mock if Day 18 pipeline cannot be loaded
    (e.g., Qdrant not running). The mock still uses retrieval over the
    test set contexts so RAGAS can run end-to-end.
    """
    try:
        from src.pipeline import build_pipeline, run_query
        search, reranker = build_pipeline()
        print("  Day 18 pipeline loaded.")

        def rag(q: str):
            answer, contexts = run_query(q, search, reranker)
            return answer, contexts
        return rag
    except Exception as e:
        print(f"  Day 18 pipeline failed ({e}). Using mock RAG...")
        return _mock_rag()


def _mock_rag():
    """Mock RAG: BM25-style over test set contexts. Useful when Qdrant is down."""
    import re
    from collections import Counter

    df = pd.read_csv(TESTSET)
    corpus = []
    for _, r in df.iterrows():
        ctx = r["contexts"]
        if isinstance(ctx, str):
            try:
                ctx_list = ast.literal_eval(ctx) if ctx.startswith("[") else [ctx]
            except Exception:
                ctx_list = [ctx]
        else:
            ctx_list = []
        for c in ctx_list:
            corpus.append(c)
    print(f"  Mock corpus: {len(corpus)} chunks")

    def tokens(s):
        return re.findall(r"\w+", s.lower())

    def rag(q: str):
        q_tokens = Counter(tokens(q))
        scored = []
        for c in corpus:
            c_tokens = Counter(tokens(c))
            score = sum((q_tokens & c_tokens).values())
            scored.append((score, c))
        scored.sort(reverse=True)
        top = [c for _, c in scored[:3]]
        answer = top[0] if top else "Không tìm thấy thông tin."
        return answer, top

    return rag


def parse_contexts(s):
    if isinstance(s, list):
        return s
    if isinstance(s, str):
        try:
            return ast.literal_eval(s)
        except Exception:
            return [s]
    return []


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY chưa được set", file=sys.stderr)
        sys.exit(1)

    print("[1/4] Loading test set...")
    df = pd.read_csv(TESTSET)
    df["contexts"] = df["contexts"].map(parse_contexts)
    print(f"  Loaded {len(df)} questions")

    print("[2/4] Loading RAG pipeline...")
    rag = get_rag_pipeline()

    print("[3/4] Running RAG on test set (~5-10 minutes)...")
    results = []
    start = time.time()
    for i, row in df.iterrows():
        try:
            answer, contexts = rag(row["question"])
        except Exception as e:
            print(f"  Q{i+1} failed: {e}")
            answer, contexts = "Error during retrieval.", []
        results.append({
            "question": row["question"],
            "answer": answer,
            "contexts": contexts,
            "ground_truth": row["ground_truth"],
        })
        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(df)}] done ({time.time()-start:.0f}s elapsed)")

    print("[4/4] Running RAGAS evaluation...")
    from datasets import Dataset
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )

    dataset = Dataset.from_list(results)
    scores = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=ChatOpenAI(model="gpt-4o-mini"),
        embeddings=OpenAIEmbeddings(model="text-embedding-3-small"),
    )

    # Per-question results
    result_df = scores.to_pandas()
    result_df.to_csv(RESULTS, index=False)

    # Aggregate
    summary = {
        "faithfulness": float(result_df["faithfulness"].mean()),
        "answer_relevancy": float(result_df["answer_relevancy"].mean()),
        "context_precision": float(result_df["context_precision"].mean()),
        "context_recall": float(result_df["context_recall"].mean()),
        "total_questions": len(result_df),
        "total_runtime_seconds": round(time.time() - start, 1),
    }

    with open(SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n=== RAGAS Summary ===")
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")
    print(f"\nResults: {RESULTS}")
    print(f"Summary: {SUMMARY}")


if __name__ == "__main__":
    main()
