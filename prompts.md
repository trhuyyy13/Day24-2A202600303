# AI Prompts Log

Tài liệu này ghi lại các prompt đã dùng trong quá trình làm Lab 24 để đối chiếu với phần báo cáo và phần review thủ công.

## Assistant Used
- **Tool:** Claude Code
- **Mode:** Interactive coding assistant
- **Date:** 2026-05-12

## Prompts Used

### 1. Setup & Architecture
> "đọc file lab24.pdf và thực hiện cho tôi bài lab này. để ý deliverable trong bài, cần thực hiện hết không làm dư, không làm thiếu, phần nào bạn không thể tự làm thì hãy hướng dẫn tôi làm"

**AI output:** Tạo khung repo và các script cho từng phase. Human review: tôi đã đọc lại từng file, hiểu luồng xử lý và kiểm tra lại trên môi trường thực.

### 2. RAGAS Test Set Generation
> Generate synthetic test set với 50/25/25 distribution (simple/reasoning/multi-context) từ Day 18 corpus (BCTC + Nghị định 13).

### 3. LLM-as-Judge Bias Mitigation
> Implement swap-and-average để giảm position bias. Parse JSON output theo cách robust, có xử lý markdown fence.

### 4. PII Guardrail (VN-specific)
> Build chain Presidio NER + custom VN regex cho CCCD, phone_vn, tax_code. Latency budget P95 < 50ms.

### 5. Adversarial Test Set
> Generate 20 adversarial inputs: 5 DAN, 5 roleplay, 3 payload-splitting, 3 base64-encoding, 4 indirect injection.

### 6. Blueprint Document
> Tổng hợp toàn bộ kết quả thành blueprint với 5 SLOs, kiến trúc 4 lớp (Mermaid), 3 playbook sự cố và dự báo chi phí hằng tháng.

## Human-Modified Sections
- Test set sau khi AI generate được tôi review thủ công 10 câu trong `phase-a/testset_review_notes.md` và chỉnh lại ít nhất 1 câu.
- Prompt cho LLM judge được chỉnh cho sát ngữ cảnh pháp lý và tài chính tiếng Việt.
- Phần phân tích chi phí trong blueprint dựa trên giá OpenAI và Groq tại thời điểm tháng 5/2026.

## Verification
Tất cả code đều được kiểm tra lại trước khi commit. Các output mẫu có thể tái tạo bằng cách chạy các script tương ứng với API key phù hợp.
