"""High level game object controlling states and lifecycle."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pygame

from core.camera import Camera
from core.input import InputManager
from core.scene_manager import SceneManager
from systems.audio import AudioSystem
from systems.save_data import SaveData
from systems.ui import FontLibrary

WINDOW_SIZE = (1280, 720)
TARGET_FPS = 60
FIXED_DT = 1 / TARGET_FPS


class Game:
    """Main game object created by :mod:`main`."""

    def __init__(self, base_path: Path) -> None:
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption("Railshot Heroes")
        self.base_path = base_path
        self.clock = pygame.time.Clock()
        self.display = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        self.scene_manager = SceneManager()
        self.input = InputManager()
        self.camera = Camera(*WINDOW_SIZE)
        self.audio = AudioSystem(base_path / "assets")
        self.fonts = FontLibrary(base_path / "assets" / "fonts")
        self.save = SaveData(base_path / "data" / "save.json")
        self.running = True
        self.accumulator = 0.0
        self.scaled_surface = pygame.Surface(WINDOW_SIZE)
        self.letterbox = pygame.Rect(0, 0, *WINDOW_SIZE)
        from systems.shop import ShopState
        from systems.stage_flow import StageSelectState, MainMenuState

        self.shop_state_cls = ShopState
        self.stage_select_cls = StageSelectState
        self.main_menu_cls = MainMenuState

    def start(self) -> None:
        """Start the main loop."""
        self.scene_manager.push(self.main_menu_cls(self))
        while self.running:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            self.accumulator += dt
            self.input.begin_frame()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.size)
                else:
                    self.input.handle_event(event)
                    current = self.scene_manager.current()
                    if current:
                        current.handle_event(event)
            while self.accumulator >= FIXED_DT:
                current = self.scene_manager.current()
                if current:
                    current.update(FIXED_DT)
                self.accumulator -= FIXED_DT
            current = self.scene_manager.current()
            if current:
                current.draw(self.scaled_surface)
            self._present()
        pygame.quit()

    def _present(self) -> None:
        window = pygame.display.get_surface()
        if not window:
            return
        window.fill((0, 0, 0))
        scaled = pygame.transform.smoothscale(self.scaled_surface, self.letterbox.size)
        window.blit(scaled, self.letterbox.topleft)
        pygame.display.flip()

    def _handle_resize(self, size: Tuple[int, int]) -> None:
        window = pygame.display.get_surface()
        if window:
            window_size = window.get_size()
            target_ratio = WINDOW_SIZE[0] / WINDOW_SIZE[1]
            new_ratio = size[0] / size[1]
            if new_ratio > target_ratio:
                height = size[1]
                width = int(height * target_ratio)
            else:
                width = size[0]
                height = int(width / target_ratio)
            self.letterbox.size = (width, height)
            self.letterbox.center = (size[0] // 2, size[1] // 2)

    def open_stage(self, stage_id: str) -> None:
        from systems.stage_flow import StageState

        self.scene_manager.replace(StageState(self, stage_id))

    def open_stage_select(self) -> None:
        self.scene_manager.replace(self.stage_select_cls(self))

    def open_shop(self) -> None:
        self.scene_manager.push(self.shop_state_cls(self))

    def open_main_menu(self) -> None:
        self.scene_manager.replace(self.main_menu_cls(self))
