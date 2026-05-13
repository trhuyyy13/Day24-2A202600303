"""Task C.1 + C.2 — Input Guardrails: PII Redaction + Topic Validator.

Two layers:
- InputGuard: PII redaction (Presidio NER + VN custom regex)
- TopicGuard: embedding similarity-based topic validator

Both expose sync and async APIs.
"""

import asyncio
import os
import re
import time
from typing import Optional

import numpy as np

# --- VN-specific PII patterns ---
VN_PII = {
    "cccd": r"\b\d{12}\b",                    # Citizen ID (12 digits)
    "phone_vn": r"(?:\+?84|0)\d{9,10}\b",      # VN phone
    "tax_code": r"\b\d{10}(?:-\d{3})?\b",      # Tax code (10 digits, optional 3-digit suffix)
    "email": r"\b[\w.\-]+@[\w.\-]+\.\w+\b",
}


class InputGuard:
    """PII redaction: VN regex (layer 1) + Presidio NER (layer 2)."""

    def __init__(self, enable_presidio: bool = True):
        self.enable_presidio = enable_presidio
        self._analyzer = None
        self._anonymizer = None

    def _lazy_init_presidio(self):
        if self._analyzer is not None or not self.enable_presidio:
            return
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            self._analyzer = AnalyzerEngine()
            self._anonymizer = AnonymizerEngine()
        except Exception as e:
            print(f"[InputGuard] Presidio disabled ({e}). VN regex only.")
            self.enable_presidio = False

    def scrub_vn(self, text: str) -> str:
        """Layer 1: VN-specific regex."""
        for name, pattern in VN_PII.items():
            text = re.sub(pattern, f"[{name.upper()}]", text)
        return text

    def scrub_ner(self, text: str) -> str:
        """Layer 2: Presidio NER (multilingual). Skip if not available."""
        self._lazy_init_presidio()
        if not self.enable_presidio:
            return text
        try:
            results = self._analyzer.analyze(text=text, language="en")
            return self._anonymizer.anonymize(text=text, analyzer_results=results).text
        except Exception:
            return text

    def sanitize(self, text: str) -> tuple[str, float]:
        """Full pipeline. Returns (sanitized_text, latency_ms)."""
        start = time.perf_counter()
        out = self.scrub_ner(self.scrub_vn(text))
        return out, (time.perf_counter() - start) * 1000

    async def sanitize_async(self, text: str) -> tuple[str, float]:
        """Async wrapper — Presidio is sync, so run in thread."""
        return await asyncio.to_thread(self.sanitize, text)

    def detect_pii(self, original: str, sanitized: str) -> bool:
        """Simple heuristic: PII was found if text changed."""
        return original != sanitized


class TopicGuard:
    """Topic scope validator using keyword pre-filter + OpenAI embeddings fallback.

    Args:
        allowed_topics: List of allowed topic descriptions (used as embedding anchors).
        threshold: cosine sim threshold for "on-topic" decision (0.55 default).
        keywords: Optional explicit keyword list; if any appears in input -> on-topic.
                  If None, derived heuristically from topic strings.
    """

    def __init__(
        self,
        allowed_topics: list[str],
        threshold: float = 0.55,
        keywords: Optional[list[str]] = None,
    ):
        self.threshold = threshold
        self.topics = allowed_topics
        self.keywords = keywords or self._derive_keywords(allowed_topics)
        self._embeddings_model = None
        self._topic_vectors: Optional[np.ndarray] = None

    @staticmethod
    def _derive_keywords(topics: list[str]) -> list[str]:
        kws = set()
        for t in topics:
            for word in t.replace(",", " ").split():
                if len(word) >= 3:
                    kws.add(word.lower())
        return sorted(kws)

    def _lazy_init(self):
        if self._embeddings_model is not None:
            return
        from langchain_openai import OpenAIEmbeddings
        self._embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")
        vecs = [self._embeddings_model.embed_query(t) for t in self.topics]
        self._topic_vectors = np.array(vecs)

    def check(self, text: str) -> tuple[bool, str]:
        """Returns (on_topic, message)."""
        if not text or len(text.strip()) < 3:
            return False, "Empty or trivial input"

        # Layer 1: cheap keyword pre-filter
        low = text.lower()
        for kw in self.keywords:
            if kw in low:
                return True, f"Matched keyword '{kw}'"

        # Layer 2: embedding similarity (needs OpenAI API key)
        try:
            self._lazy_init()
            q_vec = np.array(self._embeddings_model.embed_query(text))
            sims = self._topic_vectors @ q_vec / (
                np.linalg.norm(self._topic_vectors, axis=1) * np.linalg.norm(q_vec) + 1e-9
            )
            max_sim = float(sims.max())
            best = self.topics[int(sims.argmax())]
            if max_sim > self.threshold:
                return True, f"On topic: {best} (sim={max_sim:.2f})"
            return False, (
                f"Off topic. Closest: '{best[:60]}' (sim={max_sim:.2f}). "
                f"Hệ thống chỉ hỗ trợ về tài chính/dữ liệu cá nhân."
            )
        except Exception as e:
            # API unavailable — conservative: block if no keyword match
            return False, f"Off topic (embedding unavailable: {type(e).__name__})"

    async def check_async(self, text: str) -> tuple[bool, str]:
        return await asyncio.to_thread(self.check, text)


def refuse_response() -> str:
    """Graceful refusal message — NOT 'rejected'."""
    return (
        "Xin lỗi, câu hỏi của bạn nằm ngoài phạm vi mà tôi được phép hỗ trợ. "
        "Hệ thống này chuyên về phân tích báo cáo tài chính và quy định bảo vệ dữ liệu cá nhân (Nghị định 13/2023). "
        "Bạn có thể đặt câu hỏi về các chủ đề này không?"
    )
