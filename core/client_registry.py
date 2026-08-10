import json
from pathlib import Path
from typing import Any


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    temp_path = path.with_name(f"{path.name}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temp_path.replace(path)


class ClientRegistry:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.file_path.exists():
            initial = {"clients": [], "next_id": 1}
            self._save(initial)
            return initial
        try:
            payload = json.loads(self.file_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Registry JSON must be object")
            if "clients" not in payload or "next_id" not in payload:
                raise ValueError("Registry missing required fields")
            return payload
        except (json.JSONDecodeError, OSError, ValueError):
            fallback = {"clients": [], "next_id": 1}
            self._save(fallback)
            return fallback

    def _save(self, payload: dict[str, Any]) -> None:
        _write_json_atomic(self.file_path, payload)

    def get_or_assign_id(self, mac: str, hostname: str) -> str:
        normalized_mac = mac.strip().lower()
        for client in self._data["clients"]:
            if client["mac"] == normalized_mac:
                client["hostname"] = hostname
                self._save(self._data)
                return client["pc_id"]

        pc_id = f"PC{self._data['next_id']:02d}"
        self._data["next_id"] += 1
        self._data["clients"].append({"mac": normalized_mac, "hostname": hostname, "pc_id": pc_id})
        self._save(self._data)
        return pc_id

    def list_pc_ids(self) -> list[str]:
        pc_ids = []
        for client in self._data.get("clients", []):
            pc_id = str(client.get("pc_id", "")).strip()
            if pc_id:
                pc_ids.append(pc_id)
        return sorted(set(pc_ids))
