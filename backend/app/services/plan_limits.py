PLAN_LIMITS: dict[str, dict] = {
    "free": {
        "brands": 1,
        "queries_per_brand": 10,
        "engines": ["openai", "anthropic"],
        "competitors": 2,
        "frequency": "weekly",
        "export": False,
    },
    "pro": {
        "brands": 3,
        "queries_per_brand": 100,
        "engines": ["openai", "anthropic", "perplexity", "gemini"],
        "competitors": 10,
        "frequency": "daily",
        "export": True,
    },
    "agency": {
        "brands": 999999,
        "queries_per_brand": 500,
        "engines": ["openai", "anthropic", "perplexity", "gemini"],
        "competitors": 999999,
        "frequency": "daily",
        "export": True,
    },
}


def get_plan_limits(plan_tier: str) -> dict:
    """Return the limit configuration for a given plan tier.

    Falls back to the ``free`` tier if the tier is not recognised.
    """
    return PLAN_LIMITS.get(plan_tier, PLAN_LIMITS["free"])


def check_brand_limit(current_count: int, plan_tier: str) -> bool:
    """Return True if the user can create another brand."""
    limits = get_plan_limits(plan_tier)
    return current_count < limits["brands"]


def check_query_limit(current_count: int, plan_tier: str) -> bool:
    """Return True if the user can add another query to a brand."""
    limits = get_plan_limits(plan_tier)
    return current_count < limits["queries_per_brand"]


def check_competitor_limit(current_count: int, plan_tier: str) -> bool:
    """Return True if the user can add another competitor to a brand."""
    limits = get_plan_limits(plan_tier)
    return current_count < limits["competitors"]


def get_allowed_engines(plan_tier: str) -> list[str]:
    """Return the list of engine names available for the given plan tier."""
    limits = get_plan_limits(plan_tier)
    return limits["engines"]
