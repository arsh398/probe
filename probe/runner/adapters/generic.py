"""Generic OpenAI-compatible API adapter (for local models, LiteLLM, etc.)."""

import httpx


class GenericAdapter:
    """
    Works with any OpenAI-compatible endpoint.
    Set base_url to point to your endpoint (e.g. http://localhost:4000 for LiteLLM).
    """

    def __init__(self, base_url: str = "https://api.openai.com") -> None:
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        client: httpx.AsyncClient,
        model: str,
        api_key: str,
        messages: list[dict],
        **kwargs,
    ) -> str:
        response = await client.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages, **kwargs},
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
