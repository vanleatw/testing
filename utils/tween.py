"""Tween helpers for UI transitions."""
from __future__ import annotations

import math


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out."""
    return -t * (t - 2)


def ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in/out for smooth transitions."""
    if t < 0.5:
        return 4 * t * t * t
    f = (2 * t) - 2
    return 0.5 * f * f * f + 1


def ease_out_back(t: float, overshoot: float = 1.70158) -> float:
    """Back ease-out used for punchy pop-ups."""
    t -= 1
    return (t * t * ((overshoot + 1) * t + overshoot)) + 1


def ping_pong(t: float) -> float:
    """Ping-pong between 0 and 1."""
    return 0.5 * (1 + math.sin(2 * math.pi * (t - 0.25)))
