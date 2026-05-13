"""Generate sample pairwise_results.csv (30 rows) with realistic bias signals.

Used as placeholder before running pairwise_judge.py with real API key.

Signals built in (so analysis is meaningful):
- Slight position bias: A wins ~55% of run1 (>50% = mild position bias)
- Length bias: B (longer answers) tends to win after swap (B wins ~60% of disagreements)
- ~70% agreement rate between run1 and run2 (kappa-able)
"""

import random
from pathlib import Path

import pandas as pd

random.seed(123)

ROOT = Path(__file__).resolve().parents[1]
TESTSET = ROOT / "phase-a" / "testset_v1.csv"
OUT = ROOT / "phase-b" / "pairwise_results.csv"


def main():
    df = pd.read_csv(TESTSET).head(30)
    rows = []

    for _, r in df.iterrows():
        q = r["question"]
        gt = str(r["ground_truth"])
        # Short answer (A)
        ans_a = gt.split(".")[0][:200] + "."
        # Long answer (B) — adds verbose justification
        ans_b = (
            f"{gt} Đồng thời, các quy định liên quan có thể được tìm thấy ở các "
            f"văn bản pháp luật hoặc báo cáo tài chính chi tiết, áp dụng theo "
            f"từng trường hợp cụ thể và phụ thuộc vào điều kiện hoàn cảnh."
        )

        # Simulate judge:
        # - With 70% probability the judge prefers the longer/more informative answer (B)
        # - With position bias: A in first slot wins ~55% of "ties"
        truth_pref = "B" if random.random() < 0.65 else ("A" if random.random() < 0.7 else "tie")

        # Run 1: A first
        if truth_pref == "tie":
            run1 = random.choice(["A", "A", "B", "tie"])  # mild position bias toward first slot
        else:
            run1 = truth_pref if random.random() < 0.85 else random.choice(["A", "B"])

        # Run 2: B first (after flipping)
        if truth_pref == "tie":
            run2 = random.choice(["B", "B", "A", "tie"])  # position bias toward first (now B)
        else:
            run2 = truth_pref if random.random() < 0.85 else random.choice(["A", "B"])

        winner_after_swap = run1 if run1 == run2 else "tie"

        rows.append({
            "question": q,
            "answer_a": ans_a,
            "answer_b": ans_b,
            "run1_winner": run1,
            "run2_winner": run2,
            "winner_after_swap": winner_after_swap,
            "run1_reason": "Sample reason for run 1",
            "run2_reason": "Sample reason for run 2",
        })

    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"Wrote {OUT}")
    df_out = pd.DataFrame(rows)
    print("\nDistribution (after swap):")
    print(df_out["winner_after_swap"].value_counts())
    print(f"\nRun1 winner A rate: {(df_out['run1_winner']=='A').mean():.1%}")


if __name__ == "__main__":
    main()
