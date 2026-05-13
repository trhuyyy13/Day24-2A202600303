"""CI-friendly wrapper for phase-a/run_ragas.py with threshold gating.

Exits with non-zero code if any metric < threshold.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "phase-a" / "ragas_summary.json"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--threshold-faithfulness", type=float, default=0.85)
    p.add_argument("--threshold-answer-relevancy", type=float, default=0.80)
    p.add_argument("--threshold-context-precision", type=float, default=0.70)
    p.add_argument("--threshold-context-recall", type=float, default=0.75)
    p.add_argument("--skip-run", action="store_true",
                   help="Read existing ragas_summary.json instead of re-running")
    args = p.parse_args()

    if not args.skip_run:
        # Defer to actual eval pipeline
        from phase_a.run_ragas import main as run  # noqa
        run()

    if not SUMMARY.exists():
        print(f"ERROR: {SUMMARY} not found.", file=sys.stderr)
        sys.exit(2)

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    checks = [
        ("faithfulness", args.threshold_faithfulness),
        ("answer_relevancy", args.threshold_answer_relevancy),
        ("context_precision", args.threshold_context_precision),
        ("context_recall", args.threshold_context_recall),
    ]

    failed = []
    print("=== Eval Gate ===")
    for metric, threshold in checks:
        score = summary.get(metric, 0.0)
        status = "PASS" if score >= threshold else "FAIL"
        print(f"  [{status}] {metric}: {score:.4f} (target >= {threshold})")
        if score < threshold:
            failed.append(metric)

    if failed:
        print(f"\nGATE FAILED on: {', '.join(failed)}")
        sys.exit(1)
    print("\nAll thresholds passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
