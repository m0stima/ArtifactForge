from __future__ import annotations

from dataclasses import dataclass, field

from app.parsers.base import BaseParser
from app.parsers.generic_xml import GenericXMLParser
from app.parsers.prefetch_parser import PrefetchParser


@dataclass
class ParserRegistry:
    parsers: dict[str, BaseParser] = field(default_factory=dict)
    fallback: BaseParser = field(default_factory=GenericXMLParser)

    def __post_init__(self) -> None:
        if not self.parsers:
            self.parsers = {
                "Prefetch": PrefetchParser(),
            }

    def get(self, artifact_type: str) -> BaseParser:
        return self.parsers.get(artifact_type, self.fallback)
