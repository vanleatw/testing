"""Collectible powerups."""
from __future__ import annotations

import pygame

from actors.base import Actor


class Powerup(Actor):
    def __init__(self, position, powerup_type: str, duration: float) -> None:
        super().__init__(position)
        self.rect.size = (40, 40)
        self.rect.center = position
        self.type = powerup_type
        self.duration = duration
        self.timer = 12.0

    def update(self, dt: float, stage_state) -> None:
        super().update(dt, stage_state)
        self.timer -= dt
        if self.timer <= 0:
            self.alive = False

    def apply(self, player) -> None:
        player.apply_powerup(self.type, self.duration)

    def draw(self, surface, camera) -> None:  # pragma: no cover
        rect = camera.apply(self.rect)
        colors = {
            "rapid": (255, 200, 80),
            "spread": (80, 200, 255),
            "armor": (100, 220, 120),
            "slow": (200, 120, 255),
            "health": (255, 100, 120),
        }
        pygame.draw.rect(surface, colors.get(self.type, (200, 200, 200)), rect, border_radius=10)
