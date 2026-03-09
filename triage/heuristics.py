from __future__ import annotations

from models.artifact import ArtifactRecord
from models.finding import Finding

LOLBINS = {"powershell.exe", "cmd.exe", "rundll32.exe", "mshta.exe", "regsvr32.exe"}


class FindingsEngine:
    def evaluate(self, case_id: str, artifacts: list[ArtifactRecord]) -> list[Finding]:
        findings: list[Finding] = []
        for artifact in artifacts:
            name = str(artifact.data_json.get("name") or artifact.data_json.get("executable") or "").lower()
            path = str(artifact.data_json.get("path") or "").lower()

            if name in LOLBINS:
                findings.append(
                    Finding(
                        case_id=case_id,
                        severity="medium",
                        title="LOLBIN observed",
                        description=f"Potential dual-use binary executed: {name}",
                        artifact_id=artifact.id,
                    )
                )
            if "appdata" in path or "\\temp\\" in path:
                findings.append(
                    Finding(
                        case_id=case_id,
                        severity="high",
                        title="Process from suspicious directory",
                        description=f"Execution path indicates elevated risk: {path}",
                        artifact_id=artifact.id,
                    )
                )
            if artifact.artifact_type in {"Autoruns", "Services"} and "temp" in path:
                findings.append(
                    Finding(
                        case_id=case_id,
                        severity="high",
                        title="Suspicious persistence entry",
                        description=f"{artifact.artifact_type} points to Temp path: {path}",
                        artifact_id=artifact.id,
                    )
                )
        return findings
