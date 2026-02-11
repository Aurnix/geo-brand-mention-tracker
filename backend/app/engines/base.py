from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EngineResponse:
    raw_text: str
    model_version: str
    citations: list[str] | None = None


class BaseEngine(ABC):
    engine_name: str

    @abstractmethod
    async def run_query(self, query_text: str) -> EngineResponse:
        """Send a query and return the raw response."""
        pass
