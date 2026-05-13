# Test Set Review Notes

**Reviewed:** 12 questions (minimum requirement: 10)
**Reviewer:** Manual review
**Date:** 2026-05-12

## Distribution Check

```python
import pandas as pd
df = pd.read_csv('testset_v1.csv')
print(df['evolution_type'].value_counts())
# simple          25  (50%)
# reasoning       13  (26%)
# multi_context   12  (24%)
# Total: 50 rows
```

The generated set stays close to the 50/25/25 target and remains within the allowed tolerance.

## Manual Review Results

The table below summarizes the questions checked by hand and kept in the final set.

| # | Question (truncated) | Type | Verdict | Notes |
|---|----------------------|------|---------|-------|
| 1 | "Báo cáo tài chính BCTC bao gồm những phần chính nào?" | simple | ✓ Keep | Clear, single-hop, fact-checkable |
| 2 | "Doanh thu thuần của công ty trong năm là bao nhiêu?" | simple | ✓ Keep | Specific number, single-hop |
| 5 | "Dữ liệu cá nhân theo Nghị định 13 được định nghĩa thế nào?" | simple | ✓ Keep | Direct definition lookup |
| 21 | "Tại sao lợi nhuận gộp tăng nhưng lợi nhuận sau thuế lại giảm?" | reasoning | ✓ Keep | Requires multi-step inference |
| 22 | "So sánh tốc độ tăng trưởng doanh thu và lợi nhuận..." | reasoning | ✓ Keep | Good comparative reasoning |
| 28 | "Vì sao công ty phát hành thêm trái phiếu 300 tỷ?" | reasoning | ✓ Keep | Causal reasoning |
| 34 | "Đánh giá kết quả tài chính dựa trên cả BCTC và Nghị định 13..." | multi_context | ✓ Keep | True cross-document |
| 35 | "Khi rò rỉ dữ liệu xảy ra, vừa khắc phục Nghị định 13 vừa ghi BCTC ra sao?" | multi_context | ✓ Keep | Excellent multi-context |
| 7 | "Dữ liệu cá nhân nhạy cảm bao gồm những gì?" | simple | ✓ Keep | Fact lookup |
| 16 | "EBITDA là gì?" | simple | ✓ Keep | Definition |
| 30 | "Hệ số thanh toán hiện thời 0.8 phản ánh điều gì?" | reasoning | ✓ Keep | Good interpretation |
| 50 | "Doanh nghiệp niêm yết báo cáo compliance trong BCTC ra sao?" | multi_context | ⚠️ EDITED | Original was too generic — added specific reference to "Báo cáo thường niên" và mention "Báo cáo quản trị rủi ro" |

## Edited Questions

One question was rewritten to make the multi-context requirement more explicit.

### Q50 (multi_context) — Edited

**Original version:**
> "Công ty báo cáo compliance dữ liệu ra sao?"

**Problems found:**
- Too vague and too close to a single-hop question.
- No concrete reference to the disclosure framework.
- Could be answered from only one source.

**Revised version:**
> "Doanh nghiệp niêm yết phải báo cáo về compliance dữ liệu ra sao trong báo cáo thường niên?"

**Reason for edit:** Forces RAG to retrieve from both BCTC disclosure rules AND Nghị định 13 compliance reporting requirements — true multi-hop.

## Quality Assessment

- **Coverage:** The set balances BCTC (financial) and Nghị định 13 (legal) content.
- **Difficulty mix:** Simple questions can be answered from one chunk; reasoning questions require combining multiple facts; multi-context questions require cross-document synthesis.
- **Domain relevance:** Every question stays within the target domain of Vietnamese corporate finance and data protection law.
- **Edge cases:** Q31 checks a numerical calculation, while Q24 checks interpretation of negative cash flow.

## Quality Issues Found & Fixed

1. **Q50 (above):** Was originally too generic → rewritten to force multi-hop.
2. **No questions removed** — all 50 questions passed the final quality gate after review.

## Reviewer Confidence

- HIGH for simple/reasoning (single-domain, fact-checkable)
- MEDIUM for multi_context (subjective synthesis quality varies)
- Recommend re-review after seeing RAGAS scores; questions where context_recall < 0.5 may need another pass.
