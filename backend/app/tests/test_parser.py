"""Tests for the ResponseParser service.

The parser uses the Anthropic client for LLM calls, so we mock those.
Text-analysis methods (_name_in_text, _compute_mention_position) are tested directly.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.response_parser import ResponseParser, ParsedResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_anthropic_response(content: str):
    """Build a minimal mock of an Anthropic messages API response."""
    text_block = MagicMock()
    text_block.text = content
    response = MagicMock()
    response.content = [text_block]
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

    def test_no_false_positive_substring(self):
        """'Notion' should NOT match inside 'prenotion' or 'notional'."""
        parser = ResponseParser.__new__(ResponseParser)
        assert parser._name_in_text(["Notion"], "This is a notional concept.") is False
        assert parser._name_in_text(["Notion"], "A prenotion about the topic.") is False

    def test_no_false_positive_short_name(self):
        """Short brand names should not match within larger words."""
        parser = ResponseParser.__new__(ResponseParser)
        assert parser._name_in_text(["AI"], "I sent an email today.") is False
        assert parser._name_in_text(["Go"], "It is a good language.") is False

    def test_word_boundary_with_punctuation(self):
        """Brand names adjacent to punctuation should still match."""
        parser = ResponseParser.__new__(ResponseParser)
        assert parser._name_in_text(["Notion"], "I use Notion.") is True
        assert parser._name_in_text(["Notion"], "Notion's features are great.") is True
        assert parser._name_in_text(["Notion"], "Try Notion, it's good.") is True
        assert parser._name_in_text(["Notion"], "(Notion)") is True

    def test_word_boundary_with_hyphenated_alias(self):
        """Aliases with hyphens should match as whole tokens."""
        parser = ResponseParser.__new__(ResponseParser)
        assert parser._name_in_text(["test-brand"], "Try test-brand today.") is True


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
        parser.model = "claude-haiku-4-5-20251001"

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
        parser.model = "claude-haiku-4-5-20251001"

        # Mock the LLM response for _llm_brand_analysis
        parser.client.messages.create = AsyncMock(
            return_value=_make_anthropic_response("1. yes\n2. positive")
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
        parser.model = "claude-haiku-4-5-20251001"

        parser.client.messages.create = AsyncMock(
            return_value=_make_anthropic_response("1. no\n2. negative")
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
        parser.model = "claude-haiku-4-5-20251001"

        parser.client.messages.create = AsyncMock(
            return_value=_make_anthropic_response("1. yes\n2. positive")
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
        parser.model = "claude-haiku-4-5-20251001"

        parser.client.messages.create = AsyncMock(
            return_value=_make_anthropic_response("1. no\n2. neutral")
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
        parser.model = "claude-haiku-4-5-20251001"

        # First call: _llm_brand_analysis for the brand
        # Second call: _batch_competitor_analysis for competitors
        parser.client.messages.create = AsyncMock(
            side_effect=[
                _make_anthropic_response("1. yes\n2. positive"),
                _make_anthropic_response("CompetitorA: neutral, top=no"),
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
        assert result.competitor_mentions["CompetitorA"]["is_top_recommendation"] is False

    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_competitor_not_mentioned(self, mock_init):
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "claude-haiku-4-5-20251001"

        parser.client.messages.create = AsyncMock(
            return_value=_make_anthropic_response("1. yes\n2. positive")
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
        assert result.competitor_mentions["CompetitorA"]["is_top_recommendation"] is False

    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_competitor_is_top_recommendation(self, mock_init):
        """When the LLM says a competitor is the top recommendation, it
        should be reflected in the parsed result."""
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "claude-haiku-4-5-20251001"

        parser.client.messages.create = AsyncMock(
            side_effect=[
                _make_anthropic_response("1. no\n2. neutral"),
                _make_anthropic_response(
                    "CompetitorA: positive, top=yes\nCompetitorB: neutral, top=no"
                ),
            ]
        )

        result = await parser.parse(
            raw_response=(
                "TestBrand is okay. CompetitorA is the best option. "
                "CompetitorB is also available."
            ),
            brand_name="TestBrand",
            brand_aliases=[],
            competitors=[
                {"name": "CompetitorA", "aliases": []},
                {"name": "CompetitorB", "aliases": []},
            ],
            citations=None,
        )
        assert result.competitor_mentions["CompetitorA"]["is_top_recommendation"] is True
        assert result.competitor_mentions["CompetitorA"]["sentiment"] == "positive"
        assert result.competitor_mentions["CompetitorB"]["is_top_recommendation"] is False
        assert result.competitor_mentions["CompetitorB"]["sentiment"] == "neutral"

    @patch("app.services.response_parser.ResponseParser.__init__", return_value=None)
    async def test_citations_passed_through(self, mock_init):
        parser = ResponseParser()
        parser.client = AsyncMock()
        parser.model = "claude-haiku-4-5-20251001"

        parser.client.messages.create = AsyncMock(
            return_value=_make_anthropic_response("1. no\n2. neutral")
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
