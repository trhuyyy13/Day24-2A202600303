"""Task B.3 — Compute Cohen's Kappa between human labels and LLM judge.

Reads:
    phase-b/human_labels.csv  (10 rows with human winners)
    phase-b/pairwise_results.csv  (LLM judge results)

Output:
    phase-b/kappa_result.json
    Print interpretation
"""

import json
import sys
import io
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
HUMAN = ROOT / "phase-b" / "human_labels.csv"
JUDGE = ROOT / "phase-b" / "pairwise_results.csv"
OUT = ROOT / "phase-b" / "kappa_result.json"


def normalize(label: str) -> str:
    """Map labels to canonical form A/B/tie."""
    if not isinstance(label, str):
        return "tie"
    s = label.strip().lower()
    if s in ("a", "answer_a"):
        return "A"
    if s in ("b", "answer_b"):
        return "B"
    return "tie"


def interpret(kappa: float) -> str:
    if kappa < 0:
        return "WORSE than chance — judge có thể sai prompt hoặc human label inconsistent"
    if kappa < 0.2:
        return "Slight agreement — không tin được"
    if kappa < 0.4:
        return "Fair agreement — vẫn yếu"
    if kappa < 0.6:
        return "Moderate agreement — có thể dùng cho monitoring"
    if kappa < 0.8:
        return "Substantial agreement — production-ready"
    return "Almost perfect agreement — hiếm gặp"


def main():
    human_df = pd.read_csv(HUMAN)
    judge_df = pd.read_csv(JUDGE).head(len(human_df))

    human_labels = [normalize(x) for x in human_df["human_winner"].tolist()]
    judge_labels = [normalize(x) for x in judge_df["winner_after_swap"].tolist()]

    print(f"Human: {human_labels}")
    print(f"Judge: {judge_labels}")
    print(f"N: {len(human_labels)}")

    kappa = cohen_kappa_score(human_labels, judge_labels)
    interpretation = interpret(kappa)

    print(f"\nCohen's kappa: {kappa:.3f}")
    print(f"Interpretation: {interpretation}")

    # Disagreement details
    disagreements = []
    for i, (h, j) in enumerate(zip(human_labels, judge_labels)):
        if h != j:
            disagreements.append({
                "question_id": int(human_df.iloc[i]["question_id"]),
                "human": h,
                "judge": j,
                "human_confidence": human_df.iloc[i]["confidence"],
                "human_notes": human_df.iloc[i].get("notes", ""),
            })

    result = {
        "n_samples": len(human_labels),
        "kappa": round(kappa, 4),
        "interpretation": interpretation,
        "agreement_rate": round(sum(1 for h, j in zip(human_labels, judge_labels) if h == j) / len(human_labels), 3),
        "disagreements": disagreements,
        "production_ready": kappa >= 0.6,
    }

    if kappa < 0.6:
        result["root_cause_hypothesis"] = (
            "Kappa thấp có thể do: (1) length bias — judge có xu hướng chọn answer dài hơn; "
            "(2) human reviewer ưu tiên brevity (high conciseness); "
            "(3) judge sử dụng gpt-4o-mini, có thể không nắm bắt được nuance VN domain. "
            "Khuyến nghị: re-check prompt + label thêm 20 cặp + bias analysis trong B.4."
        )

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
