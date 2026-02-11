from app.engines.anthropic_engine import AnthropicEngine
from app.engines.gemini_engine import GeminiEngine
from app.engines.openai_engine import OpenAIEngine
from app.engines.perplexity_engine import PerplexityEngine

ENGINE_MAP: dict[str, type] = {
    "openai": OpenAIEngine,
    "anthropic": AnthropicEngine,
    "perplexity": PerplexityEngine,
    "gemini": GeminiEngine,
}
