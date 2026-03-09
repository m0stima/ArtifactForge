from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

from app.models.case import CaseModel
from app.models.base import utc_now_iso
from app.parsers.registry import ParserRegistry
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.finding_repository import FindingsRepository
from app.repositories.timeline_repository import TimelineRepository
from app.services.discovery import XMLDiscovery
from app.timeline.builder import TimelineBuilder
from app.triage.heuristics import FindingsEngine

logger = logging.getLogger(__name__)


class IndexingService:
    def __init__(
        self,
        discovery: XMLDiscovery,
        parser_registry: ParserRegistry,
        case_repo: CaseRepository,
        artifact_repo: ArtifactRepository,
        timeline_repo: TimelineRepository,
        findings_repo: FindingsRepository,
    ) -> None:
        self.discovery = discovery
        self.registry = parser_registry
        self.case_repo = case_repo
        self.artifact_repo = artifact_repo
        self.timeline_repo = timeline_repo
        self.findings_repo = findings_repo
        self.timeline_builder = TimelineBuilder()
        self.findings_engine = FindingsEngine()

    def index_case(self, case: CaseModel, progress_callback=None) -> CaseModel:
        files = self.discovery.discover(Path(case.source_path))
        collected = []
        parser_warnings = 0
        total = len(files)
        for idx, file in enumerate(files, start=1):
            artifact_type, support_state = self.discovery.classify(file)
            parser = self.registry.get(artifact_type)
            try:
                parsed = parser.parse(case.id, file, artifact_type, support_state)
                collected.extend(parsed)
                if progress_callback:
                    progress_callback(idx, total, f"Parsed {file.name} ({artifact_type})")
            except Exception as exc:
                parser_warnings += 1
                logger.warning("Parser failed for %s: %s", file, exc)
                if progress_callback:
                    progress_callback(idx, total, f"Warning: parser failure in {file.name}: {exc}")

        self.artifact_repo.insert_many(collected)
        events = self.timeline_builder.build(case.id, collected)
        self.timeline_repo.insert_many(events)
        findings = self.findings_engine.evaluate(case.id, collected)
        self.findings_repo.insert_many(findings)

        case.indexed_files_count = len(files)
        case.parser_warnings_count = parser_warnings
        case.findings_count = len(findings)
        case.timeline_events_count = len(events)
        case.artifact_counts = dict(Counter(a.artifact_type for a in collected))
        case.updated_at = utc_now_iso()
        self.case_repo.update_metrics(case)
        return case
