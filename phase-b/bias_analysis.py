"""Task B.4 — Quantify position bias + length bias from pairwise_results.csv.

Produces:
    phase-b/judge_bias_chart.png
    phase-b/judge_bias_report.md
"""

import sys
import io
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PAIRWISE = ROOT / "phase-b" / "pairwise_results.csv"
CHART = ROOT / "phase-b" / "judge_bias_chart.png"
REPORT = ROOT / "phase-b" / "judge_bias_report.md"


def main():
    df = pd.read_csv(PAIRWISE)
    total = len(df)

    # ---- Bias 1: Position bias ----
    run1_a = (df["run1_winner"] == "A").sum()
    run1_b = (df["run1_winner"] == "B").sum()
    run1_tie = (df["run1_winner"] == "tie").sum()
    # In run1, A is listed first. If judge has no position bias, A:B:tie ~ 1:1:?
    # >55% A suggests bias toward first slot.
    pos_a_rate = run1_a / total
    flipped_run2_a = (df["run2_winner"] == "A").sum()  # winner already flipped
    # In run2, B was listed first (then flipped to A in column). So if first-slot bias
    # exists, run2 should have many B (after flip, that's "A").

    # ---- Bias 2: Length bias ----
    df["len_a"] = df["answer_a"].astype(str).str.len()
    df["len_b"] = df["answer_b"].astype(str).str.len()
    df["len_diff"] = df["len_b"] - df["len_a"]

    b_when_longer = ((df["winner_after_swap"] == "B") & (df["len_diff"] > 0)).sum()
    total_b_longer = (df["len_diff"] > 0).sum()
    a_when_shorter = ((df["winner_after_swap"] == "A") & (df["len_diff"] < 0)).sum()
    total_a_shorter = (df["len_diff"] < 0).sum()

    length_bias_b = b_when_longer / total_b_longer if total_b_longer else 0
    avg_b_len = df["len_b"].mean()
    avg_a_len = df["len_a"].mean()

    # ---- Bias 3: Self-consistency (run1 == run2 rate) ----
    consistent = (df["run1_winner"] == df["run2_winner"]).sum()
    consistency_rate = consistent / total

    # ---- Print results ----
    print(f"Total samples: {total}")
    print(f"\n=== Bias 1: Position ===")
    print(f"  A wins run1 (A listed first): {run1_a}/{total} = {pos_a_rate:.1%}")
    print(f"  Expected ~50% if unbiased; >55% = position bias toward 'first' slot.")

    print(f"\n=== Bias 2: Length ===")
    print(f"  Avg length — A: {avg_a_len:.0f} chars | B: {avg_b_len:.0f} chars")
    print(f"  B wins when longer: {b_when_longer}/{total_b_longer} = {length_bias_b:.1%}")
    print(f"  Expected ~50% if no length bias.")

    print(f"\n=== Bias 3: Self-consistency ===")
    print(f"  run1 == run2: {consistent}/{total} = {consistency_rate:.1%}")
    print(f"  Lower = more position-bias-driven inconsistency.")

    # ---- Chart ----
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Plot 1: position win rates
    labels = ["A (slot 1)", "B (slot 2)", "Tie"]
    rates = [run1_a, run1_b, run1_tie]
    axes[0].bar(labels, rates, color=["#3366cc", "#dc3912", "#999"])
    axes[0].set_title(f"Run 1 winners (A in slot 1)\nPosition bias check")
    axes[0].set_ylabel("Count")
    axes[0].axhline(y=total / 2, linestyle="--", color="gray", label="50% reference")
    axes[0].legend()

    # Plot 2: length vs winner
    df["winner_after_swap"].value_counts().plot.bar(
        ax=axes[1], color=["#3366cc", "#dc3912", "#999"]
    )
    axes[1].set_title(
        f"Winner after swap\n(B avg={avg_b_len:.0f} > A avg={avg_a_len:.0f} chars)"
    )
    axes[1].set_ylabel("Count")

    plt.tight_layout()
    plt.savefig(CHART, dpi=120)
    print(f"\nChart: {CHART}")

    # ---- Report ----
    md = []
    md.append("# Judge Bias Observations Report (Task B.4)")
    md.append("")
    md.append(f"**Dataset:** `pairwise_results.csv` ({total} pairs)")
    md.append("")
    md.append("## Bias 1: Position Bias")
    md.append("")
    md.append("**Measurement:** % of times the answer in slot 1 (A position) wins in run1 (before swap).")
    md.append("")
    md.append("| Metric | Value | Expected if unbiased |")
    md.append("|---|---|---|")
    md.append(f"| A wins run1 | {run1_a}/{total} ({pos_a_rate:.1%}) | ~50% |")
    md.append(f"| B wins run1 | {run1_b}/{total} ({run1_b/total:.1%}) | ~50% |")
    md.append(f"| Ties | {run1_tie}/{total} ({run1_tie/total:.1%}) | — |")
    md.append("")
    md.append(
        "**Verdict:** "
        + (
            "⚠️ Position bias detected — judge favors the first slot."
            if pos_a_rate > 0.55
            else "✅ Position bias minimal (within ±5% of 50%)."
            if abs(pos_a_rate - 0.5) < 0.05
            else "⚠️ Slight position bias toward 'second slot' (or B-style answers) — judge picks B more often."
        )
    )
    md.append("")
    md.append("**Mitigation:** swap-and-average (B.1) reduces this — we run each pair 2x with order swapped; disagreement → tie.")
    md.append("")
    md.append("## Bias 2: Length Bias")
    md.append("")
    md.append(
        f"**Measurement:** when B's answer is longer than A's, does B win more often after swap?"
    )
    md.append("")
    md.append("| Metric | Value | Expected if unbiased |")
    md.append("|---|---|---|")
    md.append(f"| Avg length A | {avg_a_len:.0f} chars | — |")
    md.append(f"| Avg length B | {avg_b_len:.0f} chars | — |")
    md.append(f"| B wins when longer | {b_when_longer}/{total_b_longer} ({length_bias_b:.1%}) | ~50% |")
    md.append("")
    md.append(
        f"**Verdict:** "
        + (
            f"⚠️ Strong length bias — B wins {length_bias_b:.1%} of time when longer."
            if length_bias_b > 0.6
            else f"✅ Length bias minimal."
        )
    )
    md.append("")
    md.append("**Mitigation:**")
    md.append("- Add explicit prompt instruction: *'Conciseness matters — do not reward longer answers without substance.'*")
    md.append("- Re-rank pairs using a 2nd judge with a brevity-emphasizing rubric.")
    md.append("- Truncate answer_b to similar length as answer_a as a control experiment.")
    md.append("")
    md.append("## Bias 3: Self-Consistency")
    md.append("")
    md.append(f"**Measurement:** rate at which run1_winner == run2_winner (after flipping run2).")
    md.append("")
    md.append(f"- Self-consistency rate: **{consistency_rate:.1%}**")
    md.append(f"- Inconsistent pairs (resolved to tie): **{total - consistent}**")
    md.append("")
    md.append(
        "**Verdict:** "
        + (
            "✅ Judge is consistent across runs."
            if consistency_rate > 0.7
            else "⚠️ Low self-consistency — judge changes its mind based on order. Swap-and-average is essential here."
        )
    )
    md.append("")
    md.append("## Conclusion & Mitigation Strategy")
    md.append("")
    md.append("1. **Continue using swap-and-average** to neutralize position bias (effective per B.1 output).")
    md.append("2. **Strengthen rubric** to penalize verbosity — current rubric weights conciseness equally with accuracy.")
    md.append("3. **Bias-aware tie threshold** — when length difference > 1.5x, require a stronger margin to declare a winner.")
    md.append("4. **Calibration**: re-run kappa after applying mitigations; target kappa ≥ 0.6.")
    md.append("")
    md.append(f"![Bias chart]({CHART.name})")
    md.append("")

    REPORT.write_text("\n".join(md), encoding="utf-8")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
