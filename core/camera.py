"""Scrolling camera following the rail."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from utils.math import approach


@dataclass
class Camera:
    width: int
    height: int
    position: pygame.Vector2
    target_x: float = 0.0

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.position = pygame.Vector2(0, 0)
        self.target_x = 0.0

    def set_target(self, x: float) -> None:
        self.target_x = x

    def update(self, dt: float, speed: float = 600.0) -> None:
        self.position.x = approach(self.position.x, self.target_x, speed * dt)

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        offset_rect = rect.copy()
        offset_rect.x -= int(self.position.x)
        offset_rect.y -= int(self.position.y)
        return offset_rect

    def world_to_screen(self, pos: pygame.Vector2) -> pygame.Vector2:
        return pygame.Vector2(pos.x - self.position.x, pos.y - self.position.y)

    def screen_to_world(self, pos: tuple[int, int]) -> pygame.Vector2:
        return pygame.Vector2(pos[0] + self.position.x, pos[1] + self.position.y)
