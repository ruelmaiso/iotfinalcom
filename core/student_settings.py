import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def student_settings_path() -> Path:
    """Return a writable settings path for student-only runtime preferences."""
    override = os.environ.get("ESSU_SLMS_STUDENT_SETTINGS")
    if override:
        return Path(override).expanduser()
    if getattr(sys, "frozen", False):
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        return base / "ESSU-SLMS" / "student_settings.json"
    return _project_root() / "data" / "student_settings.json"


def _write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


def normalize_teacher_host(raw: str) -> str:
    host = str(raw or "").strip()
    if not host:
        raise ValueError("Teacher/Admin IP address is required.")
    if any(ch.isspace() for ch in host):
        raise ValueError("Teacher/Admin IP address cannot contain spaces.")
    if len(host) > 255:
        raise ValueError("Teacher/Admin IP address is too long.")
    return host


@dataclass
class StudentSettings:
    teacher_host: str


class StudentSettingsStore:
    def __init__(self, path: Optional[Path] = None, default_teacher_host: str = "") -> None:
        self.path = path or student_settings_path()
        self.default_teacher_host = normalize_teacher_host(default_teacher_host or "127.0.0.1")

    def load(self) -> StudentSettings:
        if not self.path.exists():
            return StudentSettings(teacher_host=self.default_teacher_host)
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return StudentSettings(
                teacher_host=normalize_teacher_host(str(payload.get("teacher_host") or self.default_teacher_host))
            )
        except Exception:
            return StudentSettings(teacher_host=self.default_teacher_host)

    def save(self, settings: StudentSettings) -> None:
        settings.teacher_host = normalize_teacher_host(settings.teacher_host)
        _write_json_atomic(self.path, asdict(settings))
