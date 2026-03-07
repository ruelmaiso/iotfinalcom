import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class AppSettings:
    main_stream_profile: str = "720p"
    preview_stream_profile: str = "360p"
    recording_mode: str = "off"  # off|manual|auto
    theme_mode: str = "light"  # light|dark|system
    reconnect_interval_s: int = 3
    heartbeat_timeout_s: int = 10
    frame_queue_policy: str = "freshest"  # freshest|drop_newest
    recording_retention_days: int = 7
    recording_max_gb: float = 5.0
    session_duration_s: int = 2 * 60 * 60
    daily_limit_s: int = 2 * 60 * 60
    enable_session_messaging: bool = False
    enable_extension_requests: bool = False
    enable_timer_near_limit_notify: bool = False
    enable_timer_pause_on_temp_lock: bool = False


class SettingsStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return AppSettings()
        defaults = asdict(AppSettings())
        defaults.update({k: v for k, v in payload.items() if k in defaults})
        return AppSettings(**defaults)

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")