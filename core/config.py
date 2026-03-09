from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class AppConfig:
    """Global application configuration."""

    app_name: str = "ArtifactForge"
    default_cases_dir: Path = Path("cases_data")
    default_db_name: str = "artifactforge.db"
    page_size: int = 200


CONFIG = AppConfig()
