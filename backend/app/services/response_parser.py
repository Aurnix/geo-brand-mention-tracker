import re
from dataclasses import dataclass, field

from openai import AsyncOpenAI

from app.config import get_settings


@dataclass
class ParsedResult:
    brand_mentioned: bool
    mention_position: str  # first, early, middle, late, not_mentioned
    is_top_recommendation: bool
    sentiment: str  # positive, neutral, negative, mixed
    competitor_mentions: dict  # {name: {mentioned, position, sentiment}}
    citations: list[str] | None


class ResponseParser:
    """Parses raw AI engine responses to extract brand mention analytics."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.PARSER_MODEL

    async def parse(
        self,
        raw_response: str,
        brand_name: str,
        brand_aliases: list[str],
        competitors: list[dict],
        citations: list[str] | None = None,
    ) -> ParsedResult:
        """Parse an AI response to extract brand mention analytics.

        Args:
            raw_response: The raw text from an AI engine.
            brand_name: Primary brand name to search for.
            brand_aliases: Alternative names / spellings for the brand.
            competitors: List of dicts with keys 'name' and 'aliases'.
            citations: Optional list of citation URLs from the engine.

        Returns:
            ParsedResult with all extracted analytics.
        """
        all_brand_names = [brand_name] + (brand_aliases or [])

        # 1. Check if brand is mentioned (case-insensitive)
        brand_mentioned = self._name_in_text(all_brand_names, raw_response)

        if not brand_mentioned:
            # Brand not mentioned -- skip expensive LLM calls, set defaults.
            competitor_mentions = await self._parse_competitor_mentions(
                raw_response, competitors
            )
            return ParsedResult(
                brand_mentioned=False,
                mention_position="not_mentioned",
                is_top_recommendation=False,
                sentiment="neutral",
                competitor_mentions=competitor_mentions,
                citations=citations,
            )

        # 2. Determine mention position
        mention_position = self._compute_mention_position(
            raw_response, all_brand_names
        )

        # 3 & 4. Run LLM calls for top recommendation and sentiment in parallel
        is_top_recommendation, sentiment = await self._llm_brand_analysis(
            raw_response, brand_name
        )

        # 5. Competitor analysis
        competitor_mentions = await self._parse_competitor_mentions(
            raw_response, competitors
        )

        return ParsedResult(
            brand_mentioned=True,
            mention_position=mention_position,
            is_top_recommendation=is_top_recommendation,
            sentiment=sentiment,
            competitor_mentions=competitor_mentions,
            citations=citations,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _name_in_text(names: list[str], text: str) -> bool:
        """Return True if any of *names* appears in *text* as a whole word
        (case-insensitive).  Uses ``\\b`` word boundaries to avoid false
        positives like matching "Notion" inside "emotional"."""
        for name in names:
            pattern = r"\b" + re.escape(name) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def _first_occurrence(names: list[str], text: str) -> int | None:
        """Return the character index of the earliest whole-word occurrence
        of any name (case-insensitive)."""
        earliest: int | None = None
        for name in names:
            pattern = r"\b" + re.escape(name) + r"\b"
            match = re.search(pattern, text, re.IGNORECASE)
            if match and (earliest is None or match.start() < earliest):
                earliest = match.start()
        return earliest

    def _compute_mention_position(
        self, text: str, brand_names: list[str]
    ) -> str:
        """Determine the position label for the first brand mention.

        Logic:
        - Find the first occurrence of any brand name/alias.
        - If it is the very first product/service/brand name mentioned in the
          entire response, label it ``"first"``.
        - Otherwise bucket the position into quartiles:
          Q1 -> "early", Q2-Q3 -> "middle", Q4 -> "late".
        """
        idx = self._first_occurrence(brand_names, text)
        if idx is None:
            return "not_mentioned"

        # Check if it's the very first notable name by seeing if there's any
        # significant word (likely a brand/product) before the first mention.
        # We use a simple heuristic: if the mention starts within the first
        # 2% of the response or nothing that looks like a proper noun appears
        # before it, treat it as "first".
        text_before = text[:idx]
        # Look for capitalized multi-char words that likely indicate a prior
        # brand/product mention (exclude common sentence-start words).
        prior_proper_nouns = re.findall(
            r"(?<![.!?\n])\s+([A-Z][a-zA-Z]{2,})", text_before
        )
        # Filter out common English words that are often capitalised at
        # sentence starts or are generic.
        common_words = {
            "The", "This", "That", "These", "Those", "There", "Here",
            "When", "Where", "What", "Which", "Who", "How", "Why",
            "For", "And", "But", "Not", "You", "Your", "Our", "Its",
            "They", "Their", "Some", "Many", "Most", "All", "Any",
            "One", "Two", "Three", "Each", "Every", "Both", "Few",
            "Several", "Other", "Another", "Such", "Like", "Also",
            "Well", "Just", "Even", "Still", "Already", "However",
            "Although", "While", "Since", "Because", "After", "Before",
            "Over", "About", "Into", "With", "From", "Have", "Has",
            "Had", "Are", "Were", "Was", "Been", "Being", "Does",
            "Did", "Will", "Would", "Could", "Should", "May", "Might",
            "Can", "Shall", "Must", "Need", "Let", "Yes", "First",
            "Second", "Third", "Now", "Then", "Next", "Last", "New",
            "Old", "Good", "Best", "Great", "High", "Low", "Long",
            "Short", "Big", "Small", "Large", "Little", "Much", "More",
        }
        prior_proper_nouns = [
            w for w in prior_proper_nouns if w not in common_words
        ]

        if not prior_proper_nouns:
            return "first"

        # Quartile-based positioning
        total_len = len(text)
        quartile_size = total_len / 4
        if idx < quartile_size:
            return "early"
        elif idx < quartile_size * 3:
            return "middle"
        else:
            return "late"

    async def _llm_brand_analysis(
        self, raw_response: str, brand_name: str
    ) -> tuple[bool, str]:
        """Run two LLM calls in a single batched request to determine
        whether the brand is the top recommendation and its sentiment.

        Returns:
            (is_top_recommendation, sentiment)
        """
        prompt = (
            f"Analyze the following AI-generated response about the brand "
            f"\"{brand_name}\".\n\n"
            f"--- BEGIN RESPONSE ---\n{raw_response}\n--- END RESPONSE ---\n\n"
            f"Answer the following two questions. Respond ONLY with two lines, "
            f"no extra text:\n"
            f"1. Is \"{brand_name}\" the top or primary recommendation? "
            f"Answer: yes or no\n"
            f"2. What is the sentiment toward \"{brand_name}\"? "
            f"Answer: positive, neutral, negative, or mixed"
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise text analyst. Follow the "
                        "instructions exactly. Output only what is asked."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=50,
        )

        answer = (response.choices[0].message.content or "").strip().lower()
        lines = [line.strip() for line in answer.splitlines() if line.strip()]

        # Parse top recommendation
        is_top = False
        if lines:
            is_top = "yes" in lines[0]

        # Parse sentiment
        sentiment = "neutral"
        valid_sentiments = {"positive", "neutral", "negative", "mixed"}
        if len(lines) >= 2:
            for word in lines[1].split():
                cleaned = re.sub(r"[^a-z]", "", word)
                if cleaned in valid_sentiments:
                    sentiment = cleaned
                    break
        elif lines:
            # Fallback: look in the single line for sentiment keywords
            for s in valid_sentiments:
                if s in lines[0]:
                    sentiment = s
                    break

        return is_top, sentiment

    async def _parse_competitor_mentions(
        self, raw_response: str, competitors: list[dict]
    ) -> dict:
        """Analyze competitor mentions in the response.

        For each competitor, determines: mentioned (bool), position (str),
        sentiment (str), and is_top_recommendation (bool).  Batches LLM
        calls for efficiency.

        Returns:
            Dict keyed by competitor name with sub-dict of analytics.
        """
        results: dict[str, dict] = {}
        mentioned_competitors: list[dict] = []

        for comp in competitors:
            comp_name = comp["name"]
            comp_aliases = comp.get("aliases", [])
            all_names = [comp_name] + (comp_aliases or [])

            mentioned = self._name_in_text(all_names, raw_response)
            if not mentioned:
                results[comp_name] = {
                    "mentioned": False,
                    "position": "not_mentioned",
                    "sentiment": "neutral",
                    "is_top_recommendation": False,
                }
            else:
                position = self._compute_mention_position(
                    raw_response, all_names
                )
                results[comp_name] = {
                    "mentioned": True,
                    "position": position,
                    "sentiment": "neutral",  # placeholder until LLM call
                    "is_top_recommendation": False,  # placeholder
                }
                mentioned_competitors.append(comp)

        # Batch LLM call for sentiment + top recommendation
        if mentioned_competitors:
            analysis = await self._batch_competitor_analysis(
                raw_response, mentioned_competitors
            )
            for comp_name, data in analysis.items():
                if comp_name in results:
                    results[comp_name]["sentiment"] = data["sentiment"]
                    results[comp_name]["is_top_recommendation"] = data[
                        "is_top_recommendation"
                    ]

        return results

    async def _batch_competitor_analysis(
        self, raw_response: str, competitors: list[dict]
    ) -> dict[str, dict]:
        """Call the LLM once to get sentiment and top-recommendation status
        for all mentioned competitors.

        Returns:
            Dict mapping competitor name -> {"sentiment": str,
            "is_top_recommendation": bool}.
        """
        comp_names = [c["name"] for c in competitors]
        numbered = "\n".join(
            f"{i + 1}. {name}" for i, name in enumerate(comp_names)
        )

        prompt = (
            f"Analyze the following AI-generated response for each of the "
            f"listed brands/products.\n\n"
            f"--- BEGIN RESPONSE ---\n{raw_response}\n--- END RESPONSE ---\n\n"
            f"Brands to analyze:\n{numbered}\n\n"
            f"For each brand, respond with the brand name followed by a colon, "
            f"then the sentiment (positive, neutral, negative, or mixed) and "
            f"whether it is the top/primary recommendation (top=yes or top=no).\n"
            f"One per line, in the same order.\n"
            f"Example format:\n"
            f"BrandA: positive, top=no\n"
            f"BrandB: neutral, top=yes"
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise text analyst. Follow the "
                        "instructions exactly. Output only what is asked."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=200,
        )

        answer = (response.choices[0].message.content or "").strip()
        valid_sentiments = {"positive", "neutral", "negative", "mixed"}
        analysis: dict[str, dict] = {}

        lines = [line.strip() for line in answer.splitlines() if line.strip()]

        for line in lines:
            if ":" in line:
                parts = line.split(":", 1)
                raw_name = parts[0].strip()
                rest = parts[1].strip().lower()

                # Parse sentiment
                sentiment = "neutral"
                for s in valid_sentiments:
                    if s in rest:
                        sentiment = s
                        break

                # Parse top recommendation
                is_top = "top=yes" in rest

                matched_name = self._match_competitor_name(
                    raw_name, comp_names
                )
                if matched_name:
                    analysis[matched_name] = {
                        "sentiment": sentiment,
                        "is_top_recommendation": is_top,
                    }

        # Ensure every mentioned competitor has an entry
        for name in comp_names:
            if name not in analysis:
                analysis[name] = {
                    "sentiment": "neutral",
                    "is_top_recommendation": False,
                }

        return analysis

    @staticmethod
    def _match_competitor_name(
        raw_name: str, known_names: list[str]
    ) -> str | None:
        """Fuzzy match the LLM-returned name to a known competitor name."""
        raw_lower = raw_name.lower().strip()
        for name in known_names:
            if name.lower() == raw_lower:
                return name
        # Partial match fallback
        for name in known_names:
            if name.lower() in raw_lower or raw_lower in name.lower():
                return name
        return None
