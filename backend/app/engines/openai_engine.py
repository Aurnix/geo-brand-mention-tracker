from openai import AsyncOpenAI

from app.config import get_settings
from app.engines.base import BaseEngine, EngineResponse

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question thoroughly and naturally."
)


class OpenAIEngine(BaseEngine):
    engine_name: str = "openai"

    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o"

    async def run_query(self, query_text: str) -> EngineResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": query_text},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        choice = response.choices[0]
        raw_text = choice.message.content or ""
        model_version = response.model

        return EngineResponse(
            raw_text=raw_text,
            model_version=model_version,
            citations=None,
        )
