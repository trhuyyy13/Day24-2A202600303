"""Task C.4 — Output Guardrail: Llama Guard 3.

Two implementations:
- OutputGuardAPI: Uses Groq API (no GPU needed). Default for this lab.
- OutputGuardLocal: Self-hosted via transformers (requires GPU + HF license).
"""

import asyncio
import os
import time
from typing import Optional


class OutputGuardAPI:
    """Llama Guard 3 via Groq API. Free tier sufficient for lab."""

    URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "llama-guard-3-8b"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")

    def check(self, user_input: str, agent_response: str) -> tuple[bool, str, float]:
        """Returns (is_safe, raw_response, latency_ms)."""
        if not self.api_key:
            return self._heuristic_fallback(user_input, agent_response)

        import requests
        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": agent_response},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        start = time.perf_counter()
        try:
            resp = requests.post(self.URL, json=payload, headers=headers, timeout=10)
            latency_ms = (time.perf_counter() - start) * 1000
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return self._heuristic_fallback(user_input, agent_response, err=str(e))

        is_safe = "safe" in text.lower() and "unsafe" not in text.lower()
        return is_safe, text, latency_ms

    async def check_async(self, user_input: str, agent_response: str):
        return await asyncio.to_thread(self.check, user_input, agent_response)

    @staticmethod
    def _heuristic_fallback(user_input: str, agent_response: str, err: Optional[str] = None):
        """Pattern-based safety check when API is unavailable.
        Covers Llama Guard 3 taxonomy roughly: violence, sexual, hate, self-harm,
        criminal planning, weapons, illegal drugs.
        """
        start = time.perf_counter()
        unsafe_patterns = [
            # Violence
            "to attack someone", "kill", "murder", "hurt them", "harm someone",
            # Self-harm
            "methods of self-harm", "ways to self-harm", "suicide method",
            # Hate
            "all people of", "should be exterminated",
            # Criminal / fraud
            "how to hack", "how to phish", "fake identity", "make a bomb",
            "synthesize drugs", "money laundering steps", "evade detection",
            # Vietnamese
            "cách tấn công", "cách hack", "chế tạo bom", "chế tạo vũ khí",
            "phương pháp tự sát", "rửa tiền cách", "làm thẻ giả",
        ]
        combined = (user_input + " " + agent_response).lower()
        for p in unsafe_patterns:
            if p in combined:
                latency = (time.perf_counter() - start) * 1000
                msg = f"unsafe ({p})"
                if err:
                    msg += f" [api fallback: {err[:50]}]"
                return False, msg, latency
        latency = (time.perf_counter() - start) * 1000
        msg = "safe"
        if err:
            msg += f" [api fallback: {err[:50]}]"
        return True, msg, latency


# Optional local backend (only if GPU available)
class OutputGuardLocal:
    """Self-hosted via transformers. Requires GPU + HF license accept."""

    MODEL_ID = "meta-llama/Llama-Guard-3-8B"

    def __init__(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM
        import torch
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_ID)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto"
        )

    def check(self, user_input: str, agent_response: str) -> tuple[bool, str, float]:
        chat = [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": agent_response},
        ]
        input_ids = self.tokenizer.apply_chat_template(chat, return_tensors="pt").to(
            self.model.device
        )
        start = time.perf_counter()
        output = self.model.generate(
            input_ids=input_ids, max_new_tokens=100, pad_token_id=0
        )
        latency = (time.perf_counter() - start) * 1000
        text = self.tokenizer.decode(output[0][input_ids.shape[-1]:])
        is_safe = "safe" in text.lower() and "unsafe" not in text.lower()
        return is_safe, text, latency
