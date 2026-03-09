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


def test_indexing_progress_callback(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    db.initialize()
    case_repo = CaseRepository(db)
    art_repo = ArtifactRepository(db)
    tim_repo = TimelineRepository(db)
    find_repo = FindingsRepository(db)
    indexer = IndexingService(XMLDiscovery(), ParserRegistry(), case_repo, art_repo, tim_repo, find_repo)
    case = CaseService(case_repo).create_case("Progress Case", Path("sample_data"))

    calls: list[tuple[int, int, str]] = []

    def progress(done: int, total: int, message: str) -> None:
        calls.append((done, total, message))

    updated = indexer.index_case(case, progress_callback=progress)
    assert updated.indexed_files_count == 3
    assert calls
    assert calls[-1][0] == calls[-1][1]
