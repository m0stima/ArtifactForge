from pathlib import Path

from cases.service import CaseService
from core.database import Database
from parsers.registry import ParserRegistry
from repositories.artifact_repository import ArtifactRepository
from repositories.case_repository import CaseRepository
from repositories.finding_repository import FindingsRepository
from repositories.timeline_repository import TimelineRepository
from services.discovery import XMLDiscovery
from services.indexer import IndexingService


def test_indexing_pipeline(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    db.initialize()
    case_repo = CaseRepository(db)
    art_repo = ArtifactRepository(db)
    tim_repo = TimelineRepository(db)
    find_repo = FindingsRepository(db)
    indexer = IndexingService(XMLDiscovery(), ParserRegistry(), case_repo, art_repo, tim_repo, find_repo)

    case = CaseService(case_repo).create_case("Unit Case", Path("sample_data"))
    updated = indexer.index_case(case)

    assert updated.indexed_files_count >= 1
    assert art_repo.query(case.id)
    assert tim_repo.list_by_case(case.id)
