"""UI drawing utilities and HUD."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pygame

from utils.tween import ease_out_back


class FontLibrary:
    """Loads fonts lazily."""

    def __init__(self, font_path: Path) -> None:
        self.font_path = font_path
        self.cache: Dict[Tuple[str, int], pygame.font.Font] = {}

    def get(self, name: str, size: int) -> pygame.font.Font:
        key = (name, size)
        if key not in self.cache:
            font_file = self.font_path / f"{name}.ttf"
            if font_file.exists():
                self.cache[key] = pygame.font.Font(str(font_file), size)
            else:
                self.cache[key] = pygame.font.SysFont(name, size)
        return self.cache[key]


@dataclass
class HUDMessage:
    text: str
    timer: float
    color: Tuple[int, int, int]


class HUD:
    """Heads-up display including combo popups and timers."""

    def __init__(self, fonts: FontLibrary) -> None:
        self.fonts = fonts
        self.messages: List[HUDMessage] = []
        self.combo_popup_time = 0.0
        self.combo_text = ""
        self.combo_scale = 0.0
        self.powerup_timers: Dict[str, float] = {}

    def set_combo(self, text: str) -> None:
        self.combo_text = text
        self.combo_popup_time = 0.8
        self.combo_scale = 0.0

    def add_message(self, text: str, color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        self.messages.append(HUDMessage(text, 2.0, color))

    def set_powerup_timer(self, name: str, time_left: float) -> None:
        self.powerup_timers[name] = time_left

    def update(self, dt: float) -> None:
        for message in list(self.messages):
            message.timer -= dt
            if message.timer <= 0:
                self.messages.remove(message)
        if self.combo_popup_time > 0:
            self.combo_popup_time -= dt
            self.combo_scale = min(1.0, self.combo_scale + dt * 3)
        else:
            self.combo_text = ""
            self.combo_scale = 0.0
        for key in list(self.powerup_timers.keys()):
            self.powerup_timers[key] = max(0.0, self.powerup_timers[key] - dt)
            if self.powerup_timers[key] == 0.0:
                self.powerup_timers.pop(key)

    def draw(self, surface: pygame.Surface, stage_state) -> None:  # pragma: no cover - drawing
        white = (230, 230, 230)
        red = (240, 80, 90)
        font_small = self.fonts.get("arial", 24)
        font_big = self.fonts.get("arial", 48)
        # Draw health hearts
        for i in range(stage_state.player.max_health):
            color = red if i < stage_state.player.health else (80, 80, 80)
            pygame.draw.circle(surface, color, (40 + i * 32, 40), 12)
        # Ammo display
        ammo_text = f"{stage_state.player.ammo}/{stage_state.player.weapon.mag_size}"
        ammo_surface = font_big.render(ammo_text, True, white)
        surface.blit(ammo_surface, (surface.get_width() - ammo_surface.get_width() - 40, surface.get_height() - 80))
        # Score
        score_surface = font_small.render(f"Score: {stage_state.score}", True, white)
        surface.blit(score_surface, (40, surface.get_height() - 60))
        # Combo popup
        if self.combo_text:
            scale = ease_out_back(self.combo_scale)
            combo_surface = font_big.render(self.combo_text, True, (255, 220, 80))
            combo_surface = pygame.transform.rotozoom(combo_surface, 0, 0.6 + 0.4 * scale)
            rect = combo_surface.get_rect(center=(surface.get_width() // 2, 120))
            surface.blit(combo_surface, rect)
        # Messages
        for idx, message in enumerate(self.messages):
            message_surface = font_small.render(message.text, True, message.color)
            surface.blit(message_surface, (40, 80 + idx * 28))
        # Powerups
        for idx, (name, time_left) in enumerate(self.powerup_timers.items()):
            timer_surface = font_small.render(f"{name}: {time_left:0.1f}s", True, (80, 200, 255))
            surface.blit(timer_surface, (surface.get_width() - 240, 80 + idx * 26))
