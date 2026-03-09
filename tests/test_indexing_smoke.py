from pathlib import Path

from app.cases.service import CaseService
from app.core.database import Database
from app.parsers.registry import ParserRegistry
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.finding_repository import FindingsRepository
from app.repositories.timeline_repository import TimelineRepository
from app.services.discovery import XMLDiscovery
from app.services.indexer import IndexingService


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
