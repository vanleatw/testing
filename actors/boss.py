"""Boss base and simple implementations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pygame

from actors.base import Actor


@dataclass
class BossPhase:
    threshold: float
    weak_spots: List[pygame.Rect]
    attack_interval: float


class Boss(Actor):
    def __init__(self, position, max_health: float, phases: List[BossPhase]) -> None:
        super().__init__(position)
        self.rect.size = (200, 200)
        self.rect.midbottom = position
        self.health = max_health
        self.max_health = max_health
        self.phases = phases
        self.phase_index = 0
        self.attack_timer = phases[0].attack_interval
        self.weak_spot = phases[0].weak_spots[0]
        self.phase_bar_rect = pygame.Rect(200, 40, 880, 16)

    def update(self, dt: float, stage_state) -> None:
        super().update(dt, stage_state)
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            stage_state.player.take_damage(2, stage_state)
            self.attack_timer = self.current_phase().attack_interval
        self._update_phase()

    def _update_phase(self) -> None:
        for idx, phase in enumerate(self.phases):
            if self.health <= self.max_health * phase.threshold:
                self.phase_index = idx
                self.weak_spot = phase.weak_spots[idx % len(phase.weak_spots)]
                self.attack_timer = max(1.0, phase.attack_interval * 0.9)

    def current_phase(self) -> BossPhase:
        return self.phases[self.phase_index]

    def take_damage(self, amount: float, stage_state, headshot: bool = False) -> None:
        weak = self.weak_spot.move(self.rect.topleft)
        cursor_world = stage_state.camera.screen_to_world(pygame.mouse.get_pos())
        if weak.collidepoint(cursor_world):
            self.health -= amount
            stage_state.spawn_hit_spark(weak.center)
            if self.health <= 0:
                self.alive = False
                stage_state.on_boss_defeated(self)
        else:
            stage_state.register_miss()

    def draw(self, surface, camera) -> None:  # pragma: no cover
        rect = camera.apply(self.rect)
        pygame.draw.rect(surface, (150, 60, 60), rect, border_radius=18)
        weak = self.weak_spot.copy()
        weak = camera.apply(weak.move(self.rect.topleft))
        pygame.draw.rect(surface, (255, 220, 80), weak, border_radius=8)
        # Health bar
        ratio = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (80, 20, 20), self.phase_bar_rect.inflate(4, 4), border_radius=6)
        pygame.draw.rect(surface, (200, 60, 60), self.phase_bar_rect, border_radius=6)
        inner = self.phase_bar_rect.copy()
        inner.width = int(inner.width * ratio)
        pygame.draw.rect(surface, (255, 160, 120), inner, border_radius=6)
