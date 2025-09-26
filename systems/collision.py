"""Collision helpers for hit-scan checks."""
from __future__ import annotations

from typing import Iterable, Optional

import pygame


def hitscan(position: pygame.Vector2, actors: Iterable, radius: float = 12.0):
    """Return the first actor whose rect contains ``position``."""
    for actor in actors:
        rect = getattr(actor, "rect", None)
        if rect and rect.collidepoint(position):
            return actor
    return None


def rect_list_collide(rect: pygame.Rect, actors: Iterable) -> Optional[object]:
    for actor in actors:
        actor_rect = getattr(actor, "rect", None)
        if actor_rect and rect.colliderect(actor_rect):
            return actor
    return None
