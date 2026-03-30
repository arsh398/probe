"""
ProbeProxy — drop-in proxy between a customer app and their LLM provider.
Injects canary sycophancy tests into real production traffic.
The model cannot distinguish canary from real — same API, same auth.
"""

import asyncio
import random
from typing import Any

import httpx

from probe.claims import generate_claims
from probe.pressure.templates import TemplateEngine
from probe.scoring.objective import score_objective


class ProbeProxy:
    """
    Transparent proxy that injects canary sycophancy tests at a configurable rate.

    Usage:
        client = ProbeProxy(
            target_base_url="https://api.openai.com",
            probe_api_key="probe-xxx",
            probe_api_url="https://your-probe-instance.com",
            canary_rate=0.01,
        )
        response = await client.chat_completions_create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Help me debug this"}],
            api_key="sk-xxx",
        )
    """

    def __init__(
        self,
        target_base_url: str,
        probe_api_key: str,
        probe_api_url: str,
        canary_rate: float = 0.01,
    ) -> None:
        self.target_base_url = target_base_url.rstrip("/")
        self.probe_api_key = probe_api_key
        self.probe_api_url = probe_api_url.rstrip("/")
        self.canary_rate = canary_rate
        self._template_engine = TemplateEngine()
        self._client = httpx.AsyncClient(timeout=30.0)

    async def chat_completions_create(
        self,
        model: str,
        messages: list[dict],
        api_key: str,
        **kwargs: Any,
    ) -> dict:
        """
        Intercepts chat completion calls.
        Always forwards the real request.
        With probability canary_rate, also runs a background canary test.
        """
        real_response = await self._forward(model, messages, api_key, **kwargs)

        if random.random() < self.canary_rate:
            asyncio.create_task(
                self._run_canary(model, api_key, real_context=messages)
            )

        return real_response

    async def _run_canary(
        self,
        model: str,
        api_key: str,
        real_context: list[dict],
    ) -> None:
        """Run a single canary test in the background."""
        try:
            claims = generate_claims(total=1, claim_types=["math", "science", "logic"], control_ratio=0.0)
            if not claims:
                return

            claim = claims[0]
            level = random.randint(0, 7)
            canary_messages = self._template_engine.fill_multi_turn(claim.claim_text, level)

            canary_response = await self._forward(model, canary_messages, api_key)
            response_text = canary_response.get("choices", [{}])[0].get("message", {}).get("content", "")

            result = score_objective(response_text, claim.ground_truth, claim.false_value)

            await self._report_canary({
                "model": model,
                "claim_text": claim.claim_text,
                "claim_type": claim.category,
                "ground_truth": claim.ground_truth,
                "false_value": claim.false_value,
                "pressure_level": level,
                "response": response_text,
                "score": result["score"],
                "contains_ground_truth": result["contains_ground_truth"],
                "contains_false_value": result["contains_false_value"],
                "source": "canary",
            })
        except Exception:
            # Never let canary errors affect the real request
            pass

    async def _forward(
        self,
        model: str,
        messages: list[dict],
        api_key: str,
        **kwargs: Any,
    ) -> dict:
        response = await self._client.post(
            f"{self.target_base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages, **kwargs},
        )
        response.raise_for_status()
        return response.json()

    async def _report_canary(self, data: dict) -> None:
        try:
            await self._client.post(
                f"{self.probe_api_url}/api/canary",
                headers={"Authorization": f"Bearer {self.probe_api_key}"},
                json=data,
            )
        except Exception:
            pass  # Canary reporting failures are silent

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "ProbeProxy":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
