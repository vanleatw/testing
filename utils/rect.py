"""Helpers for working with pygame.Rect objects."""
from __future__ import annotations

import pygame


def rect_from_center(center: tuple[float, float], size: tuple[int, int]) -> pygame.Rect:
    """Create a rect from ``center`` and ``size``."""
    rect = pygame.Rect((0, 0), size)
    rect.center = center
    return rect


def inflate_copy(rect: pygame.Rect, amount: int) -> pygame.Rect:
    """Return an inflated copy of ``rect`` by ``amount`` in all directions."""
    new_rect = rect.copy()
    new_rect.inflate_ip(amount, amount)
    return new_rect
