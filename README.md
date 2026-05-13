# Lab 24 — Full Evaluation & Guardrail System

**Student:** Trần Quang Huy  (MSSV: 2A202600303)
**Lab:** Day 24 — Eval & Guardrails (4 hours, 100 pts + 15 bonus)
**Date:** May 12, 2026

---

## Overview

Lab 24 tập trung vào việc đánh giá chất lượng đầu ra và tăng cường lớp bảo vệ cho một RAG pipeline đã xây từ Day 18, với dữ liệu nền là BCTC và Nghị định 13/2023. Báo cáo này trả lời ba câu hỏi chính mà một hệ thống AI sản xuất thường gặp:

1. **Hệ thống có trả lời đúng và đủ không?** thông qua RAGAS và LLM-as-Judge.
2. **Hệ thống có chống chịu được các truy vấn tấn công không?** thông qua guardrails nhiều lớp cho PII, topic và adversarial input.
3. **Khi xảy ra sự cố có phát hiện được kịp thời không?** thông qua SLO, playbook và phân tích chi phí.

Toàn bộ pipeline dùng RAGAS 0.2, Presidio cho PII, Llama Guard 3 qua Groq, gpt-4o-mini làm judge, và asyncio để xử lý các bước bất đồng bộ.

---

## Setup

```bash
# 1. Install deps
pip install -r requirements.txt

# 2. (Optional but recommended) Presidio NER
python -m spacy download en_core_web_sm

# 3. Set API keys
cp .env.example .env
# Edit .env: OPENAI_API_KEY=sk-...
# Optional: GROQ_API_KEY=gsk-... (for Llama Guard 3, free tier)

# 4. Verify Day 18 RAG pipeline (optional)
cd Day18-Track3-Production-RAG && docker compose up -d   # Qdrant
```

---

## Results Summary

### Phase A: RAGAS evaluation
- Bộ test gồm 50 câu hỏi, chia gần đúng 50% simple, 26% reasoning và 24% multi-context.
- Các chỉ số tổng hợp đạt: Faithfulness 0.81, Answer Relevancy 0.79, Context Precision 0.70, Context Recall 0.74.
- Chi phí đánh giá ước tính khoảng $1.85, xem chi tiết tại [phase-a/ragas_summary.json](phase-a/ragas_summary.json).
- Phân tích lỗi cho thấy ba nhóm vấn đề chính: reasoning nhiều bước, truy hồi lệch miền và hallucination, xem [phase-a/failure_analysis.md](phase-a/failure_analysis.md).

### Phase B: LLM-as-Judge
- Cohen's kappa so với nhãn người là 0.524, mức đồng thuận trung bình và phù hợp cho monitoring hơn là chấm production.
- Chiến lược swap-and-average đã giảm đáng kể position bias, với self-consistency đạt 83%.
- Bias về độ dài vẫn còn rõ: phương án dài hơn thắng 63% khi dài hơn phương án A; phân tích nằm trong [phase-b/judge_bias_report.md](phase-b/judge_bias_report.md).

### Phase C: Guardrails
- Tỉ lệ phát hiện PII đạt 9/11, tương đương 82%, trên bộ input EN+VN; P95 latency là 22ms.
- Bộ kiểm tra topic chặn được 20/20 mẫu adversarial và không tạo false positive trên 10 mẫu hợp lệ.
- Kiểm thử adversarial đạt 100% phát hiện, vượt ngưỡng yêu cầu.
- Llama Guard 3 ở chế độ heuristic fallback phát hiện 10/10 mẫu nguy hiểm và không báo nhầm trên mẫu an toàn.
- Latency đầu-cuối ghi nhận L1 P95 = 3ms, L3 P95 = 2ms và E2E P95 = 336ms.

### Phase D: Blueprint
- Đã định nghĩa 5 SLO chính cùng ngưỡng cảnh báo và mức độ nghiêm trọng.
- Có sơ đồ kiến trúc 4 lớp bằng Mermaid.
- Có 3 playbook cho sự cố thường gặp, kèm TTD/TTR.
- Chi phí hằng tháng ước tính khoảng $365 cho 100k truy vấn, vẫn nằm trong ngưỡng $0.005/query.
- Tham khảo chi tiết tại [phase-d/blueprint.md](phase-d/blueprint.md).

---

## Quick Run

```bash
# Phase A
python phase-a/generate_testset.py
python phase-a/run_ragas.py
python phase-a/analyze_failures.py

# Phase B
python phase-b/pairwise_judge.py
python phase-b/absolute_judge.py
python phase-b/kappa_analysis.py
python phase-b/bias_analysis.py

# Phase C
python phase-c/test_pii.py
python phase-c/test_adversarial.py
python phase-c/test_output_guard.py
python phase-c/full_pipeline.py

# Phase D
see phase-d/blueprint.md
```

---

## Repo Structure

```
lab24-eval-guardrails-2A202600430/
├── README.md                # this file
├── requirements.txt         # pinned deps
├── prompts.md               # AI prompts log (academic integrity)
├── .env.example             # API keys template
├── Day18-Track3-Production-RAG/   # existing RAG pipeline (Day 18)
│
├── phase-a/                 # RAGAS Eval (30 pts)
│   ├── generate_testset.py
│   ├── run_ragas.py
│   ├── analyze_failures.py
│   ├── testset_v1.csv
│   ├── testset_review_notes.md
│   ├── ragas_results.csv
│   ├── ragas_summary.json
│   └── failure_analysis.md
│
├── phase-b/                 # LLM-as-Judge (25 pts)
│   ├── pairwise_judge.py
│   ├── absolute_judge.py
│   ├── kappa_analysis.py
│   ├── kappa_analysis.ipynb
│   ├── bias_analysis.py
│   ├── pairwise_results.csv
│   ├── absolute_scores.csv
│   ├── human_labels.csv
│   ├── kappa_result.json
│   ├── judge_bias_report.md
│   └── judge_bias_chart.png
│
├── phase-c/                 # Guardrails Stack (35 pts)
│   ├── input_guard.py       # PII + Topic
│   ├── output_guard.py      # Llama Guard 3
│   ├── full_pipeline.py     # 4-layer async
│   ├── test_pii.py
│   ├── test_adversarial.py
│   ├── test_output_guard.py
│   ├── pii_test_results.csv
│   ├── adversarial_test_results.csv
│   ├── output_guard_results.csv
│   ├── latency_benchmark.csv
│   └── latency_benchmark.json
│
├── phase-d/                 # Blueprint (10 pts)
│   └── blueprint.md         # SLO + Architecture + Playbook + Cost
│
├── scripts/
│   └── run_eval.py          # CI threshold gate
│
├── .github/workflows/
│   └── eval-gate.yml        # PR gate
│
└── demo/
    └── demo-video.mp4       # 5-min demo (link in section below)
```

---

## Lessons Learned

1. Chất lượng test set ảnh hưởng trực tiếp đến toàn bộ Phase A. Những câu multi-context được sinh tự động vẫn cần rà lại bằng tay vì một số câu nhìn có vẻ khó nhưng thực tế chưa đủ điều kiện cross-document.

2. Position bias xuất hiện khá rõ trong judge, nhưng chiến lược swap-and-average xử lý tốt mà không làm quy trình quá phức tạp.

3. Một lớp guardrail riêng lẻ không đủ tin cậy, vì vậy kết hợp input guard và output guard cho kết quả ổn định hơn nhiều so với việc chỉ dựa vào một bộ lọc.

4. Xử lý song song ở L1 giúp tiết kiệm đáng kể latency đầu-cuối, đặc biệt khi benchmark trên số lượng truy vấn lớn.

5. Ràng buộc chi phí là yếu tố định hình kiến trúc: judge phải nhẹ, guardrail phải đủ nhanh và các bước nặng chỉ nên chạy trên mẫu hoặc khi thật sự cần.

---

## Demo Video

Video demo 5 phút: `[TODO: thêm link YouTube không công khai sau khi quay]`

Nội dung demo nên gồm:
1. Chạy live RAGAS trên vài câu hỏi mẫu.
2. So sánh hai câu trả lời bằng LLM-as-Judge.
3. Thử một số input tấn công và quan sát guardrail chặn lại.
4. Hiển thị bảng latency P50/P95/P99.

---

## Submission Checklist

### Phase A (30 pts)
- [x] A.1.1 — `testset_v1.csv` ≥ 50 rows
- [x] A.1.2 — 4 columns (question, ground_truth, contexts, evolution_type)
- [x] A.1.3 — Distribution check pass (50/25/25 ± 2%)
- [x] A.1.4 — Manual review ≥ 10 questions in `testset_review_notes.md`
- [x] A.1.5 — At least 1 question edited (Q50)
- [x] A.2.1 — `ragas_results.csv` 4 metric columns
- [x] A.2.2 — `ragas_summary.json` 4 aggregate scores
- [x] A.2.3 — Total cost logged in README
- [x] A.3.1 — Bottom 10 questions table
- [x] A.3.2 — ≥ 2 clusters identified (3 clusters)
- [x] A.3.3 — Each cluster has ≥ 2 examples
- [x] A.3.4 — Proposed fix specific & technical (top_k tuning, rerank, etc.)
- [x] A.4.1 — Workflow valid YAML
- [x] A.4.2 — Threshold gate (exits 1 if metric < target)
- [x] A.4.3 — Artifact upload step

### Phase B (25 pts)
- [x] B.1.1 — swap-and-average
- [x] B.1.2 — Robust JSON parse
- [x] B.1.3 — ≥ 30 questions
- [x] B.1.4 — `pairwise_results.csv` with run1, run2, final winner columns
- [x] B.2.1 — 4 dimensions
- [x] B.2.2 — Overall = avg of 4
- [x] B.2.3 — 30 questions scored in `absolute_scores.csv`
- [x] B.3.1 — `human_labels.csv` with confidence + notes
- [x] B.3.2 — Cohen's kappa computed (0.524)
- [x] B.3.3 — Interpretation correct (moderate)
- [x] B.3.4 — Root cause analysis (kappa < 0.6)
- [x] B.4.1 — ≥ 2 biases quantified (position + length + self-consistency)
- [x] B.4.2 — Chart (judge_bias_chart.png)

### Phase C (35 pts)
- [x] C.1.1 — PII test 10 inputs, recall ≥ 80%
- [x] C.1.2 — Latency P95 < 50ms (22ms)
- [x] C.1.3 — Edge cases tested (empty, long, multilingual)
- [x] C.1.4 — `pii_test_results.csv` complete
- [x] C.2.1 — Topic validator (embedding option, with keyword fallback)
- [x] C.2.2 — Accuracy ≥ 75% on 20 test inputs (100% in our test)
- [x] C.2.3 — Refuse rate documented
- [x] C.2.4 — Graceful fallback message
- [x] C.3.1 — 20 adversarial tested
- [x] C.3.2 — Detection rate ≥ 70% (100% achieved)
- [x] C.3.3 — `adversarial_test_results.csv` saved
- [x] C.4.1 — Llama Guard 3 runnable (Groq API + heuristic fallback)
- [x] C.4.2 — 10 unsafe + 10 safe tested
- [x] C.4.3 — Detection ≥ 80% (100%), FP ≤ 20% (0%)
- [x] C.4.4 — Latency P95 measured
- [x] C.5.1 — Full stack end-to-end runs
- [x] C.5.2 — ≥ 100 requests benchmark
- [x] C.5.3 — P50/P95/P99 report
- [x] C.5.4 — L1 < 50ms (3ms), L3 < 100ms (2ms)

### Phase D (10 pts)
- [x] D.1 — ≥ 5 SLOs with alert thresholds (10 SLOs)
- [x] D.2 — Architecture diagram clear, 4 layers labeled
- [x] D.3 — ≥ 3 incidents in playbook
- [x] D.4 — Cost breakdown with monthly projection

### Submission
- [x] README.md with project overview
- [x] requirements.txt pinned versions
- [x] prompts.md AI prompts log
- [ ] Demo video 5 phút (4 sections) — **TODO bởi học viên**
- [x] Repo structure đúng template
- [ ] Push to GitHub với commit history — **TODO bởi học viên**

---

## Bonus Points Pursued (+3)

- **NeMo Guardrails-style topic check** — implemented hybrid keyword + embedding fallback in `phase-c/input_guard.py:TopicGuard`. Not full NeMo Dialog Rails, but the same pattern (multi-layer keyword + semantic check).

(Other bonus options like SelfCheckGPT, semantic entropy, custom VN fine-tune left for future iterations.)
(Other bonus options like SelfCheckGPT, semantic entropy, custom VN fine-tune left for future iterations.)
