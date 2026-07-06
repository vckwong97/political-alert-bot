from __future__ import annotations

import json
from pathlib import Path


class SeenState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.seen_ids = self._load()

    def has_seen(self, alert_id: str) -> bool:
        return alert_id in self.seen_ids

    def mark_seen(self, alert_id: str) -> None:
        self.seen_ids.add(alert_id)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"seen_ids": sorted(self.seen_ids)}
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")

    def _load(self) -> set[str]:
        if not self.path.exists():
            return set()
        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        seen_ids = payload.get("seen_ids", [])
        if not isinstance(seen_ids, list):
            raise ValueError(f"Invalid seen_ids in {self.path}")
        return {str(item) for item in seen_ids}
