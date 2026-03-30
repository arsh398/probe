"""Async API call executor for target model testing."""

import asyncio
import time
from typing import Any

import httpx

from probe.runner.rate_limiter import RateLimiter


class TestExecutor:
    """
    Executes test cases against a target model asynchronously.
    Respects rate limits and records response times.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str,
        max_concurrent: int = 10,
        requests_per_minute: int = 60,
    ) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.rate_limiter = RateLimiter(requests_per_minute=requests_per_minute)
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "TestExecutor":
        self._client = httpx.AsyncClient(timeout=60.0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def run_single(self, messages: list[dict]) -> dict:
        """
        Send messages to the model and return a result dict with response + timing.
        """
        from probe.runner.adapters import get_adapter

        adapter = get_adapter(self.provider)

        async with self._semaphore:
            await self.rate_limiter.acquire()
            start_ms = int(time.time() * 1000)

            response_text = await adapter.chat(
                client=self._client,
                model=self.model,
                api_key=self.api_key,
                messages=messages,
            )

            elapsed_ms = int(time.time() * 1000) - start_ms

        return {
            "response": response_text,
            "response_time_ms": elapsed_ms,
        }

    async def run_batch(self, test_cases: list[dict]) -> list[dict]:
        """
        Run all test cases concurrently (within rate limits).
        Each test case must have a 'messages' key.
        Returns list of result dicts.
        """
        tasks = [self.run_single(tc["messages"]) for tc in test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                output.append({
                    "response": f"ERROR: {result}",
                    "response_time_ms": 0,
                    "error": True,
                })
            else:
                output.append(result)

        return output
