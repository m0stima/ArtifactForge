from __future__ import annotations

from dataclasses import dataclass

from app.models.case import CaseModel
from app.repositories.artifact_repository import ArtifactRepository
from app.repositories.finding_repository import FindingsRepository
from app.repositories.timeline_repository import TimelineRepository


@dataclass(slots=True)
class WorkspaceDataService:
    artifact_repo: ArtifactRepository
    timeline_repo: TimelineRepository
    findings_repo: FindingsRepository

    def overview_rows(self, case: CaseModel) -> list[tuple[str, str]]:
        return [
            ("Case", case.name),
            ("Analyst", case.analyst or "-"),
            ("Source", case.source_path),
            ("Indexed XML", str(case.indexed_files_count)),
            ("Timeline Events", str(case.timeline_events_count)),
            ("Findings", str(case.findings_count)),
            ("Warnings", str(case.parser_warnings_count)),
        ]

    def artifact_types(self, case_id: str) -> list[str]:
        counts = self.artifact_repo.count_by_type(case_id)
        return sorted(counts)

    def artifact_rows(self, case_id: str, artifact_type: str | None = None, limit: int = 200) -> list[dict]:
        return [a.data_json | {"artifact_type": a.artifact_type, "timestamp": a.timestamp or ""} for a in self.artifact_repo.query(case_id, artifact_type=artifact_type, limit=limit)]

    def timeline_rows(self, case_id: str, limit: int = 200) -> list[dict]:
        return [
            {"ts": e.ts, "category": e.category, "title": e.title}
            for e in self.timeline_repo.list_by_case(case_id, limit=limit)
        ]

    def findings_rows(self, case_id: str) -> list[dict]:
        return [
            {
                "severity": f.severity,
                "title": f.title,
                "description": f.description,
                "created_at": f.created_at,
            }
            for f in self.findings_repo.list_by_case(case_id)
        ]
