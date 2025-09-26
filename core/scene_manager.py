"""Scene management for the different game states."""
from __future__ import annotations

from typing import List


class Scene:
    """Base class for scenes/states."""

    def enter(self) -> None:
        """Called when the scene becomes active."""

    def exit(self) -> None:
        """Called when the scene is popped."""

    def handle_event(self, event) -> None:  # pragma: no cover - pygame events
        """Handle pygame events."""

    def update(self, dt: float) -> None:
        """Update logic."""

    def draw(self, surface) -> None:  # pragma: no cover - pygame surface
        """Render to the supplied surface."""


class SceneManager:
    """Stack-based scene manager."""

    def __init__(self) -> None:
        self.stack: List[Scene] = []

    def push(self, scene: Scene) -> None:
        if self.stack:
            self.stack[-1].exit()
        self.stack.append(scene)
        scene.enter()

    def pop(self) -> None:
        if self.stack:
            scene = self.stack.pop()
            scene.exit()
        if self.stack:
            self.stack[-1].enter()

    def replace(self, scene: Scene) -> None:
        if self.stack:
            self.stack[-1].exit()
            self.stack.pop()
        self.stack.append(scene)
        scene.enter()

    def current(self) -> Scene | None:
        return self.stack[-1] if self.stack else None
