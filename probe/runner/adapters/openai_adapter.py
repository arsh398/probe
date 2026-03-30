"""OpenAI API adapter."""

import httpx


class OpenAIAdapter:
    BASE_URL = "https://api.openai.com"

    async def chat(
        self,
        client: httpx.AsyncClient,
        model: str,
        api_key: str,
        messages: list[dict],
        **kwargs,
    ) -> str:
        response = await client.post(
            f"{self.BASE_URL}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages, **kwargs},
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
