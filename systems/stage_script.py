"""Stage scripting parsing and helpers."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List


@dataclass
class TimelineEvent:
    time: float
    action: str
    params: Dict[str, Any]


@dataclass
class StageScript:
    stage_id: str
    zone: str
    background: str
    timeline: List[TimelineEvent]
    duration: float
    music: str
    difficulty: Dict[str, float]

    @classmethod
    def from_json(cls, path: Path) -> "StageScript":
        data = json.loads(path.read_text())
        timeline = [
            TimelineEvent(time=entry["time"], action=entry["action"], params=entry.get("params", {}))
            for entry in data.get("timeline", [])
        ]
        duration = data.get("duration", max((event.time for event in timeline), default=0) + 5.0)
        return cls(
            stage_id=data["id"],
            zone=data.get("zone", "City"),
            background=data.get("background", "city"),
            timeline=sorted(timeline, key=lambda e: e.time),
            duration=duration,
            music=data.get("music", "city_theme.ogg"),
            difficulty=data.get("difficulty", {"Easy": 0.9, "Normal": 1.0, "Hard": 1.2}),
        )

    def iter_events(self) -> Iterable[TimelineEvent]:
        return iter(self.timeline)
