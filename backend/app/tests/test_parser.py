"""Tests for the ResponseParser service.

The parser uses the OpenAI client for LLM calls, so we mock those.
Text-analysis methods (_name_in_text, _compute_mention_position) are tested directly.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.response_parser import ResponseParser, ParsedResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chat_response(content: str):
    """Build a minimal mock of an OpenAI chat completion response."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


# ---------------------------------------------------------------------------
# Tests for static / non-LLM text analysis
# ---------------------------------------------------------------------------

class TestBrandMentionDetection:
    def test_brand_mentioned_exact_match(self):
        parser = ResponseParser.__new__(ResponseParser)
        text = "I recommend TestBrand for all your testing needs."
        assert parser._name_in_text(["TestBrand"], text) is True

    def test_brand_mentioned_alias(self):
        parser = ResponseParser.__new__(ResponseParser)
        text = "You should check out testbrand.com for more info."
        assert parser._name_in_text(["TestBrand", "testbrand.com"], text) is True

    def test_brand_not_mentioned(self):
        parser = ResponseParser.__new__(ResponseParser)
        text = "There are many good tools available on the market today."
        assert parser._name_in_text(["TestBrand", "testbrand.com"], text) is False

    def test_brand_mentioned_case_insensitive(self):
        parser = ResponseParser.__new__(ResponseParser)
        text = "Among the options, TESTBRAND stands out."
        assert parser._name_in_text(["TestBrand"], text) is True


class TestMentionPosition:
    def _make_parser(self):
        """Create a parser instance without calling __init__."""
        return ResponseParser.__new__(ResponseParser)

    def test_mention_position_first(self):
        parser = self._make_parser()
        # Brand appears at the very start, no prior proper nouns.
        text = "TestBrand is the leading solution for automated testing. Other tools lag behind."
        position = parser._compute_mention_position(text, ["TestBrand"])
        assert position == "first"

    def test_mention_position_early(self):
        parser = self._make_parser()
        # Another brand name (proper noun) appears before TestBrand,
        # but TestBrand is in the first quartile.
        text = (
            "Selenium is a popular framework. TestBrand is also very good. "
            + "x " * 200  # Pad text to push TestBrand into the first quartile
        )
        position = parser._compute_mention_position(text, ["TestBrand"])
        assert position in ("first", "early")

    def test_mention_position_late(self):
        parser = self._make_parser()
        # Brand appears in the last quartile of a long text.
        padding = "There are many tools. " * 100
        text = padding + " Selenium is widely used. " + padding + padding + "Finally, TestBrand is also an option."
        position = parser._compute_mention_position(text, ["TestBrand"])
        assert position == "late"

    def test_mention_position_not_mentioned(self):
        parser = self._make_parser()
        text = "No brand names here at all, just plain discussion about tools."
        position = parser._compute_mention_position(text, ["TestBrand"])
        assert position == "not_mentioned"


# ---------------------------------------------------------------------------
# Tests for the full parse() method with mocked LLM calls
# ---------------------------------------------------------------------------

class TestParseBrandNotMentioned:
    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_brand_not_mentioned_returns_defaults(self, mock_init):
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "gpt-4o-mini"

        result = await parser.parse(
            raw_response="There are many great testing tools available.",
            brand_name="TestBrand",
            brand_aliases=["testbrand.com"],
            competitors=[],
            citations=None,
        )
        assert result.brand_mentioned is False
        assert result.mention_position == "not_mentioned"
        assert result.is_top_recommendation is False
        assert result.sentiment == "neutral"


class TestSentimentParsing:
    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_sentiment_positive(self, mock_init):
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "gpt-4o-mini"

        # Mock the LLM response for _llm_brand_analysis
        parser.client.chat.completions.create = AsyncMock(
            return_value=_make_chat_response("1. yes\n2. positive")
        )

        result = await parser.parse(
            raw_response="TestBrand is amazing and the best tool.",
            brand_name="TestBrand",
            brand_aliases=[],
            competitors=[],
            citations=None,
        )
        assert result.brand_mentioned is True
        assert result.sentiment == "positive"
        assert result.is_top_recommendation is True

    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_sentiment_negative(self, mock_init):
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "gpt-4o-mini"

        parser.client.chat.completions.create = AsyncMock(
            return_value=_make_chat_response("1. no\n2. negative")
        )

        result = await parser.parse(
            raw_response="TestBrand has many issues and is not recommended.",
            brand_name="TestBrand",
            brand_aliases=[],
            competitors=[],
            citations=None,
        )
        assert result.brand_mentioned is True
        assert result.sentiment == "negative"
        assert result.is_top_recommendation is False


class TestTopRecommendation:
    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_top_recommendation_yes(self, mock_init):
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "gpt-4o-mini"

        parser.client.chat.completions.create = AsyncMock(
            return_value=_make_chat_response("1. yes\n2. positive")
        )

        result = await parser.parse(
            raw_response="TestBrand is my top recommendation for testing.",
            brand_name="TestBrand",
            brand_aliases=[],
            competitors=[],
            citations=None,
        )
        assert result.is_top_recommendation is True

    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_top_recommendation_no(self, mock_init):
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "gpt-4o-mini"

        parser.client.chat.completions.create = AsyncMock(
            return_value=_make_chat_response("1. no\n2. neutral")
        )

        result = await parser.parse(
            raw_response="TestBrand is one of several options available.",
            brand_name="TestBrand",
            brand_aliases=[],
            competitors=[],
            citations=None,
        )
        assert result.is_top_recommendation is False


class TestCompetitorMentions:
    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_competitor_mentioned(self, mock_init):
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "gpt-4o-mini"

        # First call: _llm_brand_analysis for the brand
        # Second call: _batch_competitor_sentiment for competitors
        parser.client.chat.completions.create = AsyncMock(
            side_effect=[
                _make_chat_response("1. yes\n2. positive"),
                _make_chat_response("CompetitorA: neutral"),
            ]
        )

        result = await parser.parse(
            raw_response="TestBrand is excellent. CompetitorA is also decent.",
            brand_name="TestBrand",
            brand_aliases=[],
            competitors=[{"name": "CompetitorA", "aliases": ["comp-a"]}],
            citations=None,
        )
        assert "CompetitorA" in result.competitor_mentions
        assert result.competitor_mentions["CompetitorA"]["mentioned"] is True
        assert result.competitor_mentions["CompetitorA"]["sentiment"] == "neutral"

    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_competitor_not_mentioned(self, mock_init):
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "gpt-4o-mini"

        parser.client.chat.completions.create = AsyncMock(
            return_value=_make_chat_response("1. yes\n2. positive")
        )

        result = await parser.parse(
            raw_response="TestBrand is the only tool worth mentioning.",
            brand_name="TestBrand",
            brand_aliases=[],
            competitors=[{"name": "CompetitorA", "aliases": []}],
            citations=None,
        )
        assert "CompetitorA" in result.competitor_mentions
        assert result.competitor_mentions["CompetitorA"]["mentioned"] is False

    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_citations_passed_through(self, mock_init):
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "gpt-4o-mini"

        parser.client.chat.completions.create = AsyncMock(
            return_value=_make_chat_response("1. no\n2. neutral")
        )

        citations = ["https://example.com/review"]
        result = await parser.parse(
            raw_response="TestBrand was mentioned in the review.",
            brand_name="TestBrand",
            brand_aliases=[],
            competitors=[],
            citations=citations,
        )
        assert result.citations == citations
