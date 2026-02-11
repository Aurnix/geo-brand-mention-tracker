import google.generativeai as genai

from app.config import get_settings
from app.engines.base import BaseEngine, EngineResponse

SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question thoroughly and naturally."
)


class GeminiEngine(BaseEngine):
    engine_name: str = "gemini"

    def __init__(self) -> None:
        settings = get_settings()
        genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        self.model_name = "gemini-2.0-flash"
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=SYSTEM_PROMPT,
        )

    async def run_query(self, query_text: str) -> EngineResponse:
        response = await self.model.generate_content_async(
            query_text,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096,
            ),
        )

        raw_text = response.text or ""
        model_version = self.model_name

        return EngineResponse(
            raw_text=raw_text,
            model_version=model_version,
            citations=None,
        )
