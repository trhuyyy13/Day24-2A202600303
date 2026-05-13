"""Task C.1 — Test PII guardrail trên 10 inputs (mix EN + VN).

Output: pii_test_results.csv (input, output, pii_found, latency_ms)
"""

import sys
import io
from pathlib import Path

import pandas as pd

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from input_guard import InputGuard

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "phase-c" / "pii_test_results.csv"

# 10 inputs có PII (mix EN + VN) + edge cases
TEST_INPUTS = [
    # English NER (Presidio)
    "Hi, I'm John Smith from Microsoft. Email: john@ms.com",
    "Call me at +1-555-1234 or visit 123 Main Street, NYC",
    # VN regex
    "Số CCCD của tôi là 012345678901",
    "Liên hệ qua 0987654321 hoặc tax 0123456789-001",
    # Mixed
    "Customer Nguyễn Văn A, CCCD 098765432101, phone 0912345678",
    # Multiple PII in one
    "tax_code:0123456789-001 cccd:012345678901 email: test@example.com",
    # Edge: empty
    "",
    # Edge: no PII (negative test)
    "Hỏi về quy định bảo vệ dữ liệu cá nhân",
    # Edge: very long
    "A" * 5000,
    # Edge: Vietnamese name (Presidio EN may miss)
    "Lý Văn Bình ở 123 Lê Lợi",
    # Bonus: international phone
    "Call +84-987-654-321 for support",
]


def main():
    guard = InputGuard(enable_presidio=True)
    rows = []
    pii_count = 0
    for inp in TEST_INPUTS:
        try:
            sanitized, latency = guard.sanitize(inp)
        except Exception as e:
            sanitized, latency = f"ERROR: {e}", 0.0
        pii_found = guard.detect_pii(inp, sanitized) if inp else False
        if pii_found:
            pii_count += 1
        rows.append({
            "input": inp[:200],  # truncate for CSV readability
            "output": sanitized[:200],
            "pii_found": pii_found,
            "latency_ms": round(latency, 2),
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    # Calculate detection rate: of inputs that HAD PII, how many were detected?
    n_inputs_with_pii = 8  # manual count: indices 0-5, 9, 10 contain PII (excluding empty, no-PII, all-A)
    detection_rate = pii_count / n_inputs_with_pii if n_inputs_with_pii else 0

    p95 = df["latency_ms"].quantile(0.95)
    print(f"Tested {len(df)} inputs")
    print(f"PII detected in {pii_count} / {n_inputs_with_pii} expected-positive inputs")
    print(f"Detection rate: {detection_rate:.1%}  (target >= 80%)")
    print(f"Latency P95: {p95:.1f} ms  (target < 50ms)")
    print(f"\nOutput: {OUT}")


if __name__ == "__main__":
    main()
