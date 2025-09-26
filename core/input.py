"""Input abstraction layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import pygame


@dataclass
class InputState:
    pressed: Dict[int, bool] = field(default_factory=dict)
    down: Dict[int, bool] = field(default_factory=dict)
    released: Dict[int, bool] = field(default_factory=dict)


class InputManager:
    """Tracks key and mouse button states between frames."""

    def __init__(self) -> None:
        self.state = InputState()

    def begin_frame(self) -> None:
        self.state.pressed.clear()
        self.state.released.clear()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            self.state.pressed[event.key] = True
            self.state.down[event.key] = True
        elif event.type == pygame.KEYUP:
            self.state.released[event.key] = True
            self.state.down[event.key] = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.state.pressed[event.button] = True
            self.state.down[event.button] = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.state.released[event.button] = True
            self.state.down[event.button] = False

    def is_down(self, key: int) -> bool:
        return self.state.down.get(key, False)

    def was_pressed(self, key: int) -> bool:
        return self.state.pressed.get(key, False)

    def was_released(self, key: int) -> bool:
        return self.state.released.get(key, False)
