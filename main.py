from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.cases.service import CaseService
from app.core.config import CONFIG
from app.core.database import Database
from app.core.logging import configure_logging
from app.parsers.registry import ParserRegistry
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.finding_repository import FindingsRepository
from app.repositories.timeline_repository import TimelineRepository
from app.services.discovery import XMLDiscovery
from app.services.indexer import IndexingService
from app.ui.app import ArtifactForgeApp


def build_services(db_path: Path):
    db = Database(db_path)
    db.initialize()
    case_repo = CaseRepository(db)
    artifact_repo = ArtifactRepository(db)
    timeline_repo = TimelineRepository(db)
    findings_repo = FindingsRepository(db)
    indexer = IndexingService(
        discovery=XMLDiscovery(),
        parser_registry=ParserRegistry(),
        case_repo=case_repo,
        artifact_repo=artifact_repo,
        timeline_repo=timeline_repo,
        findings_repo=findings_repo,
    )
    return db, CaseService(case_repo), case_repo, artifact_repo, timeline_repo, findings_repo, indexer


def run_self_test() -> int:
    configure_logging(logging.INFO)
    _, case_service, case_repo, artifact_repo, timeline_repo, findings_repo, indexer = build_services(Path("selftest.db"))
    print("[OK] configuration")
    print("[OK] sqlite")
    print("[OK] parser registry")

    sample = Path("sample_data")
    case = case_service.create_case("SelfTest", sample, analyst="self-test")
    case = indexer.index_case(case)

    assert case.indexed_files_count >= 1
    assert artifact_repo.query(case.id)
    assert timeline_repo.list_by_case(case.id)
    assert findings_repo.list_by_case(case.id) is not None

    print("[OK] xml parsing")
    print("[OK] indexing")
    print("[OK] timeline")
    print("[OK] findings")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="ArtifactForge")
    parser.add_argument("--self-test", action="store_true", help="Run built-in diagnostics")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    configure_logging(logging.INFO)
    ArtifactForgeApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
