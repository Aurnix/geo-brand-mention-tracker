import anthropic

from app.config import get_settings
from app.engines.base import BaseEngine, EngineResponse

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question thoroughly and naturally."
)


class AnthropicEngine(BaseEngine):
    engine_name: str = "anthropic"

    def __init__(self) -> None:
        settings = get_settings()
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    async def run_query(self, query_text: str) -> EngineResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": query_text},
            ],
        )

        # Anthropic returns a list of content blocks; concatenate text blocks.
        raw_text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        model_version = response.model

        return EngineResponse(
            raw_text=raw_text,
            model_version=model_version,
            citations=None,
        )
