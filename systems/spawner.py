"""Handles spawning actors based on stage scripts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List

from systems.stage_script import StageScript, TimelineEvent


@dataclass
class SpawnInstruction:
    event: TimelineEvent
    executed: bool = False


class Spawner:
    """Consumes :class:`StageScript` timeline events and spawns actors."""

    def __init__(self, script: StageScript, spawn_handlers: Dict[str, Callable[[TimelineEvent], None]]) -> None:
        self.events: List[SpawnInstruction] = [SpawnInstruction(event) for event in script.iter_events()]
        self.handlers = spawn_handlers
        self.elapsed = 0.0

    def reset(self) -> None:
        for event in self.events:
            event.executed = False
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt
        for instruction in self.events:
            if not instruction.executed and self.elapsed >= instruction.event.time:
                handler = self.handlers.get(instruction.event.action)
                if handler:
                    handler(instruction.event)
                instruction.executed = True
