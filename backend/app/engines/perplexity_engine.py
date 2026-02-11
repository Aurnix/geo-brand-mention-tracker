import httpx

from app.config import get_settings
from app.engines.base import BaseEngine, EngineResponse

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question thoroughly and naturally."
)

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


class PerplexityEngine(BaseEngine):
    engine_name: str = "perplexity"

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.PERPLEXITY_API_KEY
        self.model = "llama-3.1-sonar-large-128k-online"

    async def run_query(self, query_text: str) -> EngineResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query_text},
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                PERPLEXITY_API_URL, headers=headers, json=payload
            )
            resp.raise_for_status()
            data = resp.json()

        raw_text = data["choices"][0]["message"]["content"]
        model_version = data.get("model", self.model)

        # Perplexity returns citations at the top level of the response object.
        citations = data.get("citations", None)
        if citations is not None and not isinstance(citations, list):
            citations = None

        return EngineResponse(
            raw_text=raw_text,
            model_version=model_version,
            citations=citations,
        )
