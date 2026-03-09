from __future__ import annotations

from pathlib import Path


SUPPORTED_XML_HINTS = {
    "host": "Host Information",
    "user": "Users",
    "process": "Processes",
    "network": "Network Connections",
    "service": "Services",
    "driver": "Drivers",
    "task": "Scheduled Tasks",
    "autorun": "Autoruns",
    "logon": "Logon Sessions",
    "usb": "USB Devices",
    "file": "Files",
    "registry": "Registry",
    "dns": "DNS",
    "browser": "Browser Artifacts",
    "prefetch": "Prefetch",
    "amcache": "AmCache",
    "shimcache": "ShimCache / AppCompatCache",
    "recent": "Recent Files",
    "lnk": "Shortcuts / LNK",
    "jump": "Jump Lists",
    "shellbag": "Shellbags",
    "recycle": "Recycle Bin",
    "mounted": "Mounted Devices",
    "userassist": "UserAssist",
    "runmru": "RunMRU",
    "installed": "Installed Applications",
}


class XMLDiscovery:
    def discover(self, source_dir: Path) -> list[Path]:
        xml_files: list[Path] = []
        for path in source_dir.rglob("*.xml"):
            if path.suffix.lower() == ".mans" or path.name.endswith(".mans"):
                continue
            xml_files.append(path)
        return sorted(xml_files)

    def classify(self, file_path: Path) -> tuple[str, str]:
        name = file_path.name.lower()
        for token, artifact in SUPPORTED_XML_HINTS.items():
            if token in name:
                state = "supported" if artifact in {"Processes", "Network Connections", "Prefetch", "Host Information", "Users", "Services", "Autoruns", "Scheduled Tasks"} else "partial"
                return artifact, state
        return "detected_unmapped", "detected_unmapped"
