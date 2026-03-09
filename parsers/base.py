from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from models.artifact import ArtifactRecord


class BaseParser(ABC):
    parser_name: str = "base"
    artifact_type: str = "unknown"

    @abstractmethod
    def parse(self, case_id: str, source_file: Path, source_artifact_type: str, support_state: str) -> list[ArtifactRecord]:
        raise NotImplementedError
