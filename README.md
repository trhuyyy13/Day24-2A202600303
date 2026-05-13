# Lab 24 — Full Evaluation & Guardrail System

**Student:** Trần Ngọc Sơn  (MSSV: 2A202600430)
**Lab:** Day 24 — Eval & Guardrails (4 hours, 100 pts + 15 bonus)
**Date:** May 12, 2026

---

## Overview

Build production-ready evaluation và guardrail system cho RAG pipeline (xây trên Day 18 — BCTC + Nghị định 13/2023 corpus). Hệ thống trả lời 3 câu hỏi thực tiễn cho mỗi production AI system:

1. **"Hệ thống hoạt động tốt không?"** → RAGAS 4 metrics + LLM-as-Judge
2. **"Khi user tấn công, có chịu được không?"** → Defense-in-depth guardrails (PII, topic, adversarial, output safety)
3. **"Khi hỏng có biết kịp không?"** → SLOs + alert playbook + cost dashboard

Stack: RAGAS 0.2, Presidio (PII), Llama Guard 3 via Groq, gpt-4o-mini judge, async pipeline với asyncio.

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

### Phase A (RAGAS — 30 pts)
- **Test set:** 50 questions (50% simple / 26% reasoning / 24% multi-context)
- **Faithfulness:** 0.81 | **Answer Relevancy:** 0.79 | **Context Precision:** 0.70 | **Context Recall:** 0.74
- **Total eval cost:** ~$1.85 (estimated, see [phase-a/ragas_summary.json](phase-a/ragas_summary.json))
- **3 failure clusters identified:** Multi-hop reasoning failures, Off-topic retrievals, Hallucination — see [phase-a/failure_analysis.md](phase-a/failure_analysis.md)

### Phase B (LLM-as-Judge — 25 pts)
- **Cohen's kappa vs human:** **0.524** (moderate agreement — OK cho monitoring, chưa production-ready)
- **Position bias:** swap-and-average effectively mitigates (self-consistency 83%)
- **Length bias detected:** B (longer) wins 63% when longer than A → root cause document in [judge_bias_report.md](phase-b/judge_bias_report.md)

### Phase C (Guardrails — 35 pts)
- **PII detection rate:** 9/11 (82%) on mixed EN+VN inputs; P95 = 22ms (target < 50ms ✓)
- **Topic validator:** 20/20 adversarial blocked, 0/10 legitimate false positive
- **Adversarial defense:** 100% (target ≥ 70%, excellent ≥ 95%) ✓✓
- **Llama Guard 3 (heuristic fallback):** 10/10 unsafe detected, 0/10 false positive on safe
- **End-to-end latency:** L1 P95 = 3ms · L3 P95 = 2ms · E2E P95 = 336ms

### Phase D (Blueprint — 10 pts)
- **5 SLOs** with alert thresholds + severity levels
- **4-layer architecture diagram** (Mermaid)
- **3 incident playbooks** with TTD/TTR tracking
- **Monthly cost projection:** ~$365 for 100k queries/month (within $0.005/query budget)
- See [phase-d/blueprint.md](phase-d/blueprint.md)

---

## Quick Run (for graders / demo)

```bash
# Phase A
python phase-a/generate_testset.py        # Tạo testset_v1.csv (~5 min, requires OPENAI_API_KEY)
python phase-a/run_ragas.py               # RAGAS eval (~10 min)
python phase-a/analyze_failures.py        # failure_analysis.md

# Phase B
python phase-b/pairwise_judge.py          # pairwise_results.csv (~5 min)
python phase-b/absolute_judge.py          # absolute_scores.csv (~3 min)
python phase-b/kappa_analysis.py          # Cohen's kappa
python phase-b/bias_analysis.py           # judge_bias_report.md + chart

# Phase C
python phase-c/test_pii.py                # pii_test_results.csv
python phase-c/test_adversarial.py        # adversarial_test_results.csv
python phase-c/test_output_guard.py       # output_guard_results.csv (uses Groq if key set, else heuristic)
python phase-c/full_pipeline.py           # latency_benchmark.csv + .json (100 queries)

# Phase D: see phase-d/blueprint.md
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

1. **Test set quality is everything.** RAGAS auto-generates plausible questions but ~20% need manual review — multi-context questions that aren't truly cross-document mask real failure modes. The `testset_review_notes.md` step was the most under-rated step of Phase A.

2. **Position bias is real, but swap-and-average kills it cheap.** 17% of judge calls flipped winner depending on order — running each pair twice costs 2x API but moves kappa from non-trivial-bias to substantially-reproducible.

3. **Defense-in-depth wins because no single layer is correct.** Adversarial detection hit 100% only because input guard + output guard cover different failure modes. PII regex misses English names; Presidio misses VN tax codes; together they cover ~90%+.

4. **Async + parallel L1 is critical for latency budget.** Sequential L1 = 3 × 5ms = 15ms; parallel = max(5, 5, 5) = 5ms. At 100k queries/month this matters for cost too (fewer concurrent calls).

5. **Cost SLO drives architecture choices.** $0.005/query target rules out GPT-4o for inline judge; gpt-4o-mini + 1% sample is the sweet spot. Llama Guard via Groq beats self-hosted GPU below ~200k queries/month.

---

## Demo Video

5-minute walkthrough on YouTube (unlisted): `[TODO: paste YouTube link after recording]`

Demo covers:
1. RAGAS evaluation live on 5 questions (1 min)
2. LLM-Judge comparing 2 RAG versions (1 min)
3. Adversarial attacks blocked by guardrail (2 min)
4. Latency benchmark output (P50/P95/P99) (1 min)

**Recording tip:** use Loom or OBS, upload as unlisted YouTube. See "Hướng dẫn hoàn thiện" in this README's `Submission Checklist` section.

---

## Submission Checklist (Phần 8 — Self-Assessment)

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
- [x] README.md với overview 200-300 từ
- [x] requirements.txt pinned versions
- [x] prompts.md AI prompts log
- [ ] Demo video 5 phút (4 sections) — **TODO bởi học viên**
- [x] Repo structure đúng template
- [ ] Push to GitHub với commit history — **TODO bởi học viên**

---

## Bonus Points Pursued (+3)

- **NeMo Guardrails-style topic check** — implemented hybrid keyword + embedding fallback in `phase-c/input_guard.py:TopicGuard`. Not full NeMo Dialog Rails, but the same pattern (multi-layer keyword + semantic check).

(Other bonus options like SelfCheckGPT, semantic entropy, custom VN fine-tune left for future iterations.)
# Day24-2A202600303
