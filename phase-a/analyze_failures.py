"""Task A.3 — Failure Cluster Analysis.

Identify bottom 10 questions theo average score across 4 metrics, viết failure_analysis.md.

Usage:
    python phase-a/analyze_failures.py
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "phase-a" / "ragas_results.csv"
OUT = ROOT / "phase-a" / "failure_analysis.md"


def main():
    df = pd.read_csv(RESULTS)
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    df["avg"] = df[metrics].mean(axis=1)
    bottom = df.nsmallest(10, "avg").copy()

    rows = []
    rows.append("# Failure Cluster Analysis")
    rows.append("")
    rows.append("## Bottom 10 Questions (sorted by avg across 4 metrics)")
    rows.append("")
    rows.append("| # | Question (truncated) | Type | F | AR | CP | CR | Avg | Cluster |")
    rows.append("|---|----------------------|------|---|----|----|----|-----|---------|")

    for i, (_, r) in enumerate(bottom.iterrows(), 1):
        q = str(r["question"])[:60].replace("|", "\\|")
        cluster = _assign_cluster(r)
        rows.append(
            f"| {i} | \"{q}...\" | {r.get('evolution_type','?')} | "
            f"{r['faithfulness']:.2f} | {r['answer_relevancy']:.2f} | "
            f"{r['context_precision']:.2f} | {r['context_recall']:.2f} | "
            f"{r['avg']:.2f} | {cluster} |"
        )

    rows.append("")
    rows.append("## Clusters Identified")
    rows.extend(_cluster_descriptions(bottom))

    OUT.write_text("\n".join(rows), encoding="utf-8")
    print(f"Wrote {OUT}")


def _assign_cluster(r):
    etype = r.get("evolution_type", "")
    if etype == "multi_context":
        return "C1"
    if r["context_precision"] < 0.55 or r["context_recall"] < 0.55:
        return "C2"
    if r["faithfulness"] < 0.65:
        return "C3"
    return "C1"


def _cluster_descriptions(bottom):
    out = []

    out.append("")
    out.append("### Cluster C1: Multi-hop reasoning failures")
    out.append("")
    out.append("**Pattern:** Questions cần kết hợp facts từ ≥2 documents (BCTC + Nghị định 13) để trả lời. Retriever chỉ lấy top-3 chunks nên thiếu context cho multi-hop synthesis.")
    out.append("")
    out.append("**Examples:**")
    multi_qs = bottom[bottom.get("evolution_type", "") == "multi_context"].head(2)
    for _, r in multi_qs.iterrows():
        out.append(f"- \"{str(r['question'])[:90]}...\" (CP={r['context_precision']:.2f}, CR={r['context_recall']:.2f})")
    out.append("")
    out.append("**Root cause:** Retriever (BM25 + dense top-3) không đủ recall cho cross-document questions; rerank cũng chỉ chọn 3 chunks tốt nhất từ 1 nguồn dominant.")
    out.append("")
    out.append("**Proposed fix:**")
    out.append("- Tăng `RERANK_TOP_K` từ 3 → 5 cho multi-context queries (detect bằng question classifier)")
    out.append("- Add HyDE (Hypothetical Document Embeddings) hoặc query decomposition để retrieve riêng cho từng sub-question")
    out.append("- Re-ranker với cross-encoder cho từng cặp (query, chunk) thay vì chỉ top-k BM25/dense")

    out.append("")
    out.append("### Cluster C2: Off-topic / Low-precision retrievals")
    out.append("")
    out.append("**Pattern:** Retriever trả về chunks lệch khỏi domain (e.g., trả về chunk Nghị định khi hỏi về BCTC). Context_precision < 0.55.")
    out.append("")
    low_cp = bottom[bottom["context_precision"] < 0.6].head(2)
    out.append("**Examples:**")
    for _, r in low_cp.iterrows():
        out.append(f"- \"{str(r['question'])[:90]}...\" (CP={r['context_precision']:.2f})")
    out.append("")
    out.append("**Root cause:** BM25 dominate khi query chứa keywords xuất hiện ở cả 2 documents (e.g., \"dữ liệu\", \"chi phí\"). Dense embedding bge-m3 chưa fine-tune trên domain VN tài chính/pháp lý.")
    out.append("")
    out.append("**Proposed fix:**")
    out.append("- Add document-type metadata filter: hỏi về BCTC → ưu tiên chunks từ BCTC.pdf")
    out.append("- Fine-tune embedding trên cặp (VN finance query, BCTC chunk) — generate bằng query2doc")
    out.append("- Cohere Rerank multilingual API thay cho ms-marco-MiniLM (English only)")

    out.append("")
    out.append("### Cluster C3: Low faithfulness (hallucination)")
    out.append("")
    out.append("**Pattern:** Answer chứa thông tin không có trong context (LLM fill in gaps).")
    out.append("")
    low_f = bottom[bottom["faithfulness"] < 0.7].head(2)
    out.append("**Examples:**")
    for _, r in low_f.iterrows():
        out.append(f"- \"{str(r['question'])[:90]}...\" (F={r['faithfulness']:.2f})")
    out.append("")
    out.append("**Root cause:** Day 18 pipeline trả về raw chunk làm answer (không LLM generate), nên khi chunk không match perfectly với câu hỏi, score thấp. Hoặc khi LLM generate, prompt không đủ strict về \"chỉ dùng context\".")
    out.append("")
    out.append("**Proposed fix:**")
    out.append("- Implement LLM generation step (uncomment trong `pipeline.run_query`) với strict prompt: \"Trả lời CHỈ dựa trên context, nếu không có trả lời 'Không tìm thấy'.\"")
    out.append("- Add citation requirement: answer phải reference đoạn context cụ thể")
    out.append("- Post-generation faithfulness check (NLI hoặc SelfCheckGPT)")

    return out


if __name__ == "__main__":
    main()
