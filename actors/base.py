"""Base classes for actors."""
from __future__ import annotations

from typing import Tuple

import pygame


class Actor:
    def __init__(self, position: Tuple[float, float]) -> None:
        self.position = pygame.Vector2(position)
        self.rect = pygame.Rect(0, 0, 64, 64)
        self.rect.center = position
        self.alive = True

    def update(self, dt: float, stage_state) -> None:
        self.rect.center = (int(self.position.x), int(self.position.y))

    def draw(self, surface: pygame.Surface, camera) -> None:  # pragma: no cover - drawing
        raise NotImplementedError

    def take_damage(self, amount: float, stage_state, headshot: bool = False) -> None:
        pass
