"""Achievement tracking."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    condition: Callable[[dict], bool]


ACHIEVEMENTS: Dict[str, Achievement] = {
    "no_miss_50": Achievement(
        "no_miss_50",
        "No-Miss 50",
        "Finish a stage with 50 consecutive hits.",
        lambda stats: stats.get("best_combo", 0) >= 50,
    ),
    "pacifist_rescue": Achievement(
        "pacifist_rescue",
        "Pacifist Rescue",
        "Save all civilians in a stage without shooting them.",
        lambda stats: stats.get("hostages_saved", 0) > 0 and stats.get("hostages_lost", 0) == 0,
    ),
    "explosive_expert": Achievement(
        "explosive_expert",
        "Explosive Expert",
        "Defeat three enemies with barrels in one stage.",
        lambda stats: stats.get("barrel_multi_kill", 0) >= 3,
    ),
}


def evaluate_achievements(save_data, stats: dict) -> None:
    """Check and unlock achievements based on ``stats``."""
    for achievement in ACHIEVEMENTS.values():
        if achievement.condition(stats):
            save_data.unlock_achievement(achievement.id)
