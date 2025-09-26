"""Hostage actor that can be rescued or harmed."""
from __future__ import annotations

import pygame

from actors.base import Actor


class Hostage(Actor):
    def __init__(self, position) -> None:
        super().__init__(position)
        self.rect.size = (60, 100)
        self.rect.midbottom = position
        self.rope_rect = pygame.Rect(0, 0, 10, 40)
        self.rope_rect.midtop = self.rect.midtop
        self.rescued = False

    def take_damage(self, amount: float, stage_state, headshot: bool = False) -> None:
        if not self.rescued:
            stage_state.on_hostage_hit(self)
            self.alive = False

    def rescue(self, stage_state) -> None:
        if not self.rescued:
            self.rescued = True
            stage_state.on_hostage_rescued(self)
            self.alive = False

    def update(self, dt: float, stage_state) -> None:
        super().update(dt, stage_state)
        self.rope_rect.midtop = self.rect.midtop

    def draw(self, surface, camera) -> None:  # pragma: no cover
        rect = camera.apply(self.rect)
        rope = camera.apply(self.rope_rect)
        pygame.draw.rect(surface, (200, 180, 80), rope)
        pygame.draw.rect(surface, (180, 220, 120), rect, border_radius=12)
        head = pygame.Rect(0, 0, rect.width // 2, rect.height // 3)
        head.midbottom = rect.midtop
        pygame.draw.ellipse(surface, (240, 220, 180), head)
