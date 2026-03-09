from __future__ import annotations

from app.models.artifact import ArtifactRecord
from app.models.timeline import TimelineEvent


CATEGORY_MAP = {
    "Processes": "process",
    "Network Connections": "network",
    "Autoruns": "persistence",
    "Logon Sessions": "logon",
    "Services": "service",
    "USB Devices": "usb",
    "Prefetch": "system",
}


class TimelineBuilder:
    def build(self, case_id: str, artifacts: list[ArtifactRecord]) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        for artifact in artifacts:
            if not artifact.timestamp:
                continue
            category = CATEGORY_MAP.get(artifact.artifact_type, "system")
            title = f"{artifact.artifact_type}: {artifact.data_json.get('name') or artifact.data_json.get('executable') or 'event'}"
            events.append(
                TimelineEvent(
                    case_id=case_id,
                    category=category,
                    ts=artifact.timestamp,
                    title=title,
                    details_json=artifact.data_json,
                    source_artifact_id=artifact.id,
                )
            )
        return events
