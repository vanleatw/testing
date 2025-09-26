"""Save data management."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


DEFAULT_SAVE = {
    "coins": 0,
    "weapons": {"pistol": True, "smg": False, "shotgun": False, "carbine": False},
    "upgrades": {},
    "completed_stages": {},
    "settings": {"volume": 0.7, "music_volume": 0.5, "difficulty": "Normal"},
    "achievements": {},
}


@dataclass
class SaveData:
    path: Path
    data: Dict = field(default_factory=lambda: json.loads(json.dumps(DEFAULT_SAVE)))

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except json.JSONDecodeError:
                self.data = json.loads(json.dumps(DEFAULT_SAVE))
        else:
            self.write()

    def write(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2))

    def add_coins(self, amount: int) -> None:
        self.data["coins"] = self.data.get("coins", 0) + amount
        self.write()

    def unlock_weapon(self, weapon_id: str) -> None:
        self.data.setdefault("weapons", {})[weapon_id] = True
        self.write()

    def set_upgrade_level(self, upgrade_id: str, level: int) -> None:
        self.data.setdefault("upgrades", {})[upgrade_id] = level
        self.write()

    def set_stage_result(self, stage_id: str, stars: int, score: int) -> None:
        self.data.setdefault("completed_stages", {})[stage_id] = {"stars": stars, "score": score}
        self.write()

    def achievement_unlocked(self, achievement_id: str) -> bool:
        return self.data.get("achievements", {}).get(achievement_id, False)

    def unlock_achievement(self, achievement_id: str) -> None:
        if not self.achievement_unlocked(achievement_id):
            self.data.setdefault("achievements", {})[achievement_id] = True
            self.write()

    def update_settings(self, **kwargs) -> None:
        settings = self.data.setdefault("settings", {})
        settings.update(kwargs)
        self.write()

    def get_completed_stages(self) -> Dict[str, Dict[str, int]]:
        return self.data.get("completed_stages", {})

    def get_weapon_unlocks(self) -> Dict[str, bool]:
        return self.data.get("weapons", {})

    def get_upgrade(self, upgrade_id: str) -> int:
        return self.data.get("upgrades", {}).get(upgrade_id, 0)

    def reset(self) -> None:
        self.data = json.loads(json.dumps(DEFAULT_SAVE))
        self.write()
