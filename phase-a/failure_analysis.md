# Failure Analysis

## Lowest-Scoring Questions

The table below highlights the 10 questions with the weakest average score across the four metrics.

| # | Question (truncated) | Type | F | AR | CP | CR | Avg | Cluster |
|---|----------------------|------|---|----|----|----|-----|---------|
| 1 | "Việc chuyển dữ liệu cá nhân ra nước ngoài có ảnh hưởng đến c..." | multi_context | 0.63 | 0.74 | 0.31 | 0.56 | 0.56 | C1 |
| 2 | "Kết hợp thông tin BCTC + Nghị định 13: doanh nghiệp nên ưu t..." | multi_context | 0.46 | 0.74 | 0.58 | 0.53 | 0.58 | C1 |
| 3 | "Mức độ trưởng thành về bảo vệ dữ liệu của doanh nghiệp có th..." | multi_context | 0.69 | 0.51 | 0.62 | 0.61 | 0.61 | C1 |
| 4 | "Tại sao lợi nhuận gộp tăng nhưng lợi nhuận sau thuế lại giảm..." | reasoning | 0.71 | 0.75 | 0.46 | 0.60 | 0.63 | C2 |
| 5 | "Tỷ lệ đầu tư cho compliance dữ liệu cá nhân chiếm bao nhiêu ..." | multi_context | 0.61 | 0.77 | 0.62 | 0.54 | 0.63 | C1 |
| 6 | "Trường hợp doanh nghiệp niêm yết bị xử phạt vi phạm dữ liệu,..." | multi_context | 0.55 | 0.76 | 0.63 | 0.69 | 0.66 | C1 |
| 7 | "Khoản chi phí cho hệ thống bảo vệ dữ liệu cá nhân nên được p..." | multi_context | 0.53 | 0.73 | 0.52 | 0.90 | 0.67 | C1 |
| 8 | "Nếu công ty con vi phạm bảo vệ dữ liệu, công ty mẹ cần ghi n..." | multi_context | 0.72 | 0.99 | 0.27 | 0.72 | 0.68 | C1 |
| 9 | "Nếu rò rỉ dữ liệu dẫn đến kiện tụng, doanh nghiệp xử lý kế t..." | multi_context | 0.85 | 0.78 | 0.40 | 0.69 | 0.68 | C1 |
| 10 | "Khi doanh nghiệp M&A một công ty xử lý nhiều dữ liệu cá nhân..." | multi_context | 0.78 | 0.83 | 0.44 | 0.67 | 0.68 | C1 |

## Clusters Identified

### Cluster C1: Multi-hop reasoning gaps

**Pattern:** These questions need facts from at least two documents, usually BCTC and Nghị định 13. With only the top-3 chunks, the retriever often misses enough context for a complete answer.

**Examples:**
- "Việc chuyển dữ liệu cá nhân ra nước ngoài có ảnh hưởng đến chi phí hoạt động kinh doanh đư..." (CP=0.31, CR=0.56)
- "Kết hợp thông tin BCTC + Nghị định 13: doanh nghiệp nên ưu tiên xếp hạng rủi ro nào cao nh..." (CP=0.58, CR=0.53)

**Root cause:** The BM25 + dense retriever does not recall enough cross-document context. Reranking still tends to keep only three chunks from the dominant source.

**Proposed fix:**
- Tăng `RERANK_TOP_K` từ 3 → 5 cho multi-context queries (detect bằng question classifier)
- Add HyDE (Hypothetical Document Embeddings) hoặc query decomposition để retrieve riêng cho từng sub-question
- Re-ranker với cross-encoder cho từng cặp (query, chunk) thay vì chỉ top-k BM25/dense

### Cluster C2: Off-topic / low-precision retrievals

**Pattern:** The retriever sometimes returns chunks from the wrong source, for example a Nghị định chunk when the question is about BCTC. Context precision then drops below 0.55.

**Examples:**
- "Việc chuyển dữ liệu cá nhân ra nước ngoài có ảnh hưởng đến chi phí hoạt động kinh doanh đư..." (CP=0.31)
- "Kết hợp thông tin BCTC + Nghị định 13: doanh nghiệp nên ưu tiên xếp hạng rủi ro nào cao nh..." (CP=0.58)

**Root cause:** BM25 dominates when the query contains keywords shared by both documents, such as “dữ liệu” or “chi phí”. The bge-m3 embedding model also has not been tuned for Vietnamese finance and legal text.

**Proposed fix:**
- Add document-type metadata filter: hỏi về BCTC → ưu tiên chunks từ BCTC.pdf
- Fine-tune embedding trên cặp (VN finance query, BCTC chunk) — generate bằng query2doc
- Cohere Rerank multilingual API thay cho ms-marco-MiniLM (English only)

### Cluster C3: Low faithfulness

**Pattern:** The answer includes information that is not supported by the retrieved context.

**Examples:**
- "Việc chuyển dữ liệu cá nhân ra nước ngoài có ảnh hưởng đến chi phí hoạt động kinh doanh đư..." (F=0.63)
- "Kết hợp thông tin BCTC + Nghị định 13: doanh nghiệp nên ưu tiên xếp hạng rủi ro nào cao nh..." (F=0.46)

**Root cause:** The Day 18 pipeline may return raw chunks instead of a fully grounded generated answer, so partial matches score poorly. When generation is used, the prompt still needs tighter context-only instructions.

**Proposed fix:**
- Implement LLM generation step (uncomment trong `pipeline.run_query`) với strict prompt: "Trả lời CHỈ dựa trên context, nếu không có trả lời 'Không tìm thấy'."
- Add citation requirement: answer phải reference đoạn context cụ thể
- Post-generation faithfulness check (NLI hoặc SelfCheckGPT)