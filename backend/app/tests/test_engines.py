"""Tests for engine adapters.

Uses mocks to verify engine instantiation and response handling
without making real API calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.engines.base import BaseEngine, EngineResponse
from app.engines import ENGINE_MAP


class TestEngineMap:
    def test_all_engines_registered(self):
        """ENGINE_MAP should contain all four engines."""
        assert "openai" in ENGINE_MAP
        assert "anthropic" in ENGINE_MAP
        assert "perplexity" in ENGINE_MAP
        assert "gemini" in ENGINE_MAP

    def test_engine_map_values_are_classes(self):
        """Each value in ENGINE_MAP should be a class (not an instance)."""
        for name, cls in ENGINE_MAP.items():
            assert isinstance(cls, type), f"{name} is not a class"

    def test_all_engines_subclass_base(self):
        """All engine classes should subclass BaseEngine."""
        for name, cls in ENGINE_MAP.items():
            assert issubclass(cls, BaseEngine), f"{name} doesn't subclass BaseEngine"


class TestOpenAIEngine:
    @patch("app.engines.openai_engine.AsyncOpenAI")
    async def test_run_query_returns_engine_response(self, mock_openai_cls):
        """OpenAI engine should return an EngineResponse."""
        from app.engines.openai_engine import OpenAIEngine

        mock_client = AsyncMock()
        mock_openai_cls.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = "TestBrand is great for project management."
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion = MagicMock()
        mock_completion.choices = [mock_choice]
        mock_completion.model = "gpt-5.2"

        mock_client.chat.completions.create.return_value = mock_completion

        engine = OpenAIEngine()
        result = await engine.run_query("What is the best project management tool?")

        assert isinstance(result, EngineResponse)
        assert "TestBrand" in result.raw_text
        assert result.model_version == "gpt-5.2"


class TestAnthropicEngine:
    @patch("app.engines.anthropic_engine.anthropic")
    async def test_run_query_returns_engine_response(self, mock_anthropic_mod):
        """Anthropic engine should return an EngineResponse."""
        from app.engines.anthropic_engine import AnthropicEngine

        mock_client = AsyncMock()
        mock_anthropic_mod.AsyncAnthropic.return_value = mock_client

        mock_block = MagicMock()
        mock_block.text = "TestBrand is mentioned frequently."
        mock_block.type = "text"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_response.model = "claude-sonnet-4-20250514"

        mock_client.messages.create.return_value = mock_response

        engine = AnthropicEngine()
        result = await engine.run_query("Tell me about project tools")

        assert isinstance(result, EngineResponse)
        assert "TestBrand" in result.raw_text


class TestGeminiEngine:
    @patch("app.engines.gemini_engine.genai")
    async def test_run_query_returns_engine_response(self, mock_genai):
        """Gemini engine should return an EngineResponse."""
        from app.engines.gemini_engine import GeminiEngine

        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini recommends TestBrand."
        # generate_content_async is awaited, so it needs to be an AsyncMock
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_genai.GenerativeModel.return_value = mock_model

        engine = GeminiEngine()
        result = await engine.run_query("Best tools?")

        assert isinstance(result, EngineResponse)
        assert "TestBrand" in result.raw_text
