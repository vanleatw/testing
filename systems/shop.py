"""Shop and upgrade state."""
from __future__ import annotations

import json
from typing import Dict, List

import pygame

from core.scene_manager import Scene


class ShopState(Scene):
    def __init__(self, game) -> None:
        self.game = game
        self.font_title = game.fonts.get("arial", 48)
        self.font = game.fonts.get("arial", 28)
        self.weapons = self._load_json("weapons.json")
        self.upgrades = self._load_json("upgrades.json")
        self.selection_index = 0
        self.items = self.weapons + self.upgrades

    def _load_json(self, filename: str) -> List[Dict]:
        path = self.game.base_path / "data" / filename
        if path.exists():
            return json.loads(path.read_text())
        return []

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.game.scene_manager.pop()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selection_index = (self.selection_index + 1) % len(self.items)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selection_index = (self.selection_index - 1) % len(self.items)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._purchase_selected()

    def _purchase_selected(self) -> None:
        if not self.items:
            return
        item = self.items[self.selection_index]
        cost = item.get("cost", 0)
        if self.game.save.data.get("coins", 0) < cost:
            return
        if item.get("type") == "weapon":
            if not self.game.save.get_weapon_unlocks().get(item["id"], False):
                self.game.save.add_coins(-cost)
                self.game.save.unlock_weapon(item["id"])
        else:
            level = self.game.save.get_upgrade(item["id"])
            self.game.save.add_coins(-cost)
            self.game.save.set_upgrade_level(item["id"], level + 1)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        surface.fill((26, 26, 30))
        title = self.font_title.render("Shop", True, (255, 220, 160))
        surface.blit(title, (60, 60))
        coins = self.font.render(f"Coins: {self.game.save.data.get('coins', 0)}", True, (220, 220, 220))
        surface.blit(coins, (surface.get_width() - coins.get_width() - 60, 60))
        if not self.items:
            empty = self.font.render("No items available", True, (200, 200, 200))
            surface.blit(empty, (60, 160))
            return
        for idx, item in enumerate(self.items):
            color = (255, 255, 255) if idx == self.selection_index else (160, 160, 170)
            owned = False
            if item.get("type") == "weapon":
                owned = self.game.save.get_weapon_unlocks().get(item["id"], False)
            else:
                owned = self.game.save.get_upgrade(item["id"]) > 0
            label = f"{item['name']} - {item['cost']} coins"
            if owned:
                label += " (Owned)"
            text = self.font.render(label, True, color)
            surface.blit(text, (60, 160 + idx * 40))
            desc = self.font.render(item.get("description", ""), True, (120, 140, 160))
            surface.blit(desc, (80, 190 + idx * 40))
