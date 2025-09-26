"""Interactive objects like explosive barrels and crates."""
from __future__ import annotations

import pygame

from actors.base import Actor


class ExplosiveBarrel(Actor):
    def __init__(self, position) -> None:
        super().__init__(position)
        self.rect.size = (50, 70)
        self.rect.midbottom = position
        self.health = 30

    def take_damage(self, amount: float, stage_state, headshot: bool = False) -> None:
        self.health -= amount
        if self.health <= 0 and self.alive:
            self.alive = False
            stage_state.on_barrel_exploded(self)

    def draw(self, surface, camera) -> None:  # pragma: no cover
        rect = camera.apply(self.rect)
        pygame.draw.rect(surface, (200, 80, 60), rect, border_radius=6)
        pygame.draw.rect(surface, (255, 200, 80), rect.inflate(-10, -10), 0, border_radius=4)


class CoinCrate(Actor):
    def __init__(self, position, coins: int = 10) -> None:
        super().__init__(position)
        self.rect.size = (60, 60)
        self.rect.midbottom = position
        self.coins = coins

    def take_damage(self, amount: float, stage_state, headshot: bool = False) -> None:
        if self.alive:
            self.alive = False
            stage_state.on_coin_crate_broken(self)

    def draw(self, surface, camera) -> None:  # pragma: no cover
        rect = camera.apply(self.rect)
        pygame.draw.rect(surface, (200, 180, 60), rect, border_radius=8)
        pygame.draw.rect(surface, (120, 80, 20), rect.inflate(-8, -8), 2, border_radius=6)
