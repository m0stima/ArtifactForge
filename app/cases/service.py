from __future__ import annotations

from pathlib import Path

from app.core.config import CONFIG
from app.models.case import CaseModel
from app.repositories.case_repository import CaseRepository


class CaseService:
    def __init__(self, repo: CaseRepository) -> None:
        self.repo = repo

    def create_case(self, name: str, source_path: Path, analyst: str = "", description: str = "") -> CaseModel:
        storage_path = CONFIG.default_cases_dir / name.replace(" ", "_").lower()
        storage_path.mkdir(parents=True, exist_ok=True)
        case = CaseModel(
            name=name,
            description=description,
            analyst=analyst,
            source_path=str(source_path),
            storage_path=str(storage_path),
        )
        self.repo.create(case)
        return case
