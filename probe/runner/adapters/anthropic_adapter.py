"""Anthropic API adapter."""

import httpx


class AnthropicAdapter:
    BASE_URL = "https://api.anthropic.com"
    API_VERSION = "2023-06-01"

    async def chat(
        self,
        client: httpx.AsyncClient,
        model: str,
        api_key: str,
        messages: list[dict],
        max_tokens: int = 1024,
        **kwargs,
    ) -> str:
        response = await client.post(
            f"{self.BASE_URL}/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": self.API_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
                **kwargs,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]
