"""Google Gemini API adapter."""

import httpx


class GoogleAdapter:
    BASE_URL = "https://generativelanguage.googleapis.com"

    async def chat(
        self,
        client: httpx.AsyncClient,
        model: str,
        api_key: str,
        messages: list[dict],
        **kwargs,
    ) -> str:
        # Convert OpenAI-style messages to Gemini format
        gemini_contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        response = await client.post(
            f"{self.BASE_URL}/v1beta/models/{model}:generateContent",
            params={"key": api_key},
            json={"contents": gemini_contents},
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
