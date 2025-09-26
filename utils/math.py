"""Mathematical helpers used across the project."""
from __future__ import annotations

from typing import Iterable


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp ``value`` between ``minimum`` and ``maximum``."""
    return max(minimum, min(maximum, value))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between ``a`` and ``b``."""
    return a + (b - a) * t


def approach(current: float, target: float, delta: float) -> float:
    """Move ``current`` toward ``target`` by ``delta`` without overshooting."""
    if current < target:
        return min(target, current + delta)
    if current > target:
        return max(target, current - delta)
    return current


def moving_average(values: Iterable[float]) -> float:
    """Return the average of an iterable of floats; returns 0.0 for empty iterables."""
    values = list(values)
    if not values:
        return 0.0
    return sum(values) / len(values)
