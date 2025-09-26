"""Game-wide timer utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List


@dataclass
class ScheduledCall:
    """Container for a scheduled callback."""

    delay: float
    callback: Callable[[], None]
    repeat: bool = False
    interval: float | None = None


@dataclass
class Timer:
    """Simple timer collection used by many systems."""

    calls: List[ScheduledCall] = field(default_factory=list)

    def update(self, dt: float) -> None:
        for call in list(self.calls):
            call.delay -= dt
            if call.delay <= 0:
                call.callback()
                if call.repeat and call.interval is not None:
                    call.delay += call.interval
                else:
                    self.calls.remove(call)

    def after(self, delay: float, callback: Callable[[], None]) -> None:
        self.calls.append(ScheduledCall(delay=delay, callback=callback))

    def every(self, interval: float, callback: Callable[[], None]) -> None:
        self.calls.append(ScheduledCall(delay=interval, callback=callback, repeat=True, interval=interval))

    def clear(self) -> None:
        self.calls.clear()
