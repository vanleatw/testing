"""Game states related to stages and menus."""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import pygame

from actors.boss import Boss, BossPhase
from actors.enemies import ENEMY_FACTORIES, Enemy
from actors.hostage import Hostage
from actors.objects import CoinCrate, ExplosiveBarrel
from actors.player import Player, WEAPON_DATA
from actors.powerup import Powerup
from core.scene_manager import Scene
from systems.achievements import ACHIEVEMENTS, evaluate_achievements
from systems.particles import ParticleSystem
from systems.spawner import Spawner
from systems.stage_script import StageScript
from systems.ui import HUD
from utils.math import clamp

BUTTON_LEFT = 1
BUTTON_RIGHT = 3


class MainMenuState(Scene):
    def __init__(self, game) -> None:
        self.game = game
        self.font_title = game.fonts.get("arial", 64)
        self.font = game.fonts.get("arial", 32)
        self.options = ["Play", "Shop", "Achievements", "Settings", "Quit"]
        self.selection = 0

    def enter(self) -> None:
        self.game.audio.play_music("menu", loop=True)

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selection = (self.selection + 1) % len(self.options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selection = (self.selection - 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_option()

    def _activate_option(self) -> None:
        option = self.options[self.selection]
        if option == "Play":
            self.game.open_stage_select()
        elif option == "Shop":
            self.game.open_shop()
        elif option == "Achievements":
            self.game.scene_manager.push(AchievementState(self.game))
        elif option == "Settings":
            self.game.scene_manager.push(SettingsState(self.game))
        elif option == "Quit":
            self.game.running = False

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        surface.fill((18, 22, 30))
        title = self.font_title.render("Railshot Heroes", True, (255, 220, 120))
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 160))
        for idx, option in enumerate(self.options):
            color = (255, 255, 255) if idx == self.selection else (140, 140, 160)
            text = self.font.render(option, True, color)
            surface.blit(text, (surface.get_width() // 2 - text.get_width() // 2, 300 + idx * 60))


class SettingsState(Scene):
    def __init__(self, game) -> None:
        self.game = game
        self.font = game.fonts.get("arial", 32)
        self.slider = game.save.data["settings"].get("volume", 0.7)
        self.music_slider = game.save.data["settings"].get("music_volume", 0.5)
        self.difficulty = game.save.data["settings"].get("difficulty", "Normal")
        self.difficulties = ["Easy", "Normal", "Hard"]

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.game.scene_manager.pop()
            elif event.key == pygame.K_LEFT:
                self.slider = clamp(self.slider - 0.1, 0.0, 1.0)
            elif event.key == pygame.K_RIGHT:
                self.slider = clamp(self.slider + 0.1, 0.0, 1.0)
            elif event.key == pygame.K_DOWN:
                self.music_slider = clamp(self.music_slider - 0.1, 0.0, 1.0)
            elif event.key == pygame.K_UP:
                self.music_slider = clamp(self.music_slider + 0.1, 0.0, 1.0)
            elif event.key == pygame.K_TAB:
                idx = self.difficulties.index(self.difficulty)
                self.difficulty = self.difficulties[(idx + 1) % len(self.difficulties)]
            self.game.save.update_settings(volume=self.slider, music_volume=self.music_slider, difficulty=self.difficulty)
            self.game.audio.set_master_volume(self.slider)
            self.game.audio.set_music_volume(self.music_slider)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        surface.fill((20, 24, 28))
        title = self.font.render("Settings", True, (255, 220, 120))
        surface.blit(title, (60, 80))
        volume = self.font.render(f"SFX Volume: {self.slider:.1f} (Left/Right)", True, (220, 220, 220))
        surface.blit(volume, (60, 160))
        music = self.font.render(f"Music Volume: {self.music_slider:.1f} (Up/Down)", True, (220, 220, 220))
        surface.blit(music, (60, 220))
        difficulty = self.font.render(f"Difficulty: {self.difficulty} (Tab)", True, (220, 220, 220))
        surface.blit(difficulty, (60, 280))
        hint = self.font.render("Esc to return", True, (160, 160, 160))
        surface.blit(hint, (60, surface.get_height() - 80))


class AchievementState(Scene):
    def __init__(self, game) -> None:
        self.game = game
        self.font_title = game.fonts.get("arial", 48)
        self.font = game.fonts.get("arial", 28)

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            self.game.scene_manager.pop()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        surface.fill((16, 18, 26))
        title = self.font_title.render("Achievements", True, (255, 220, 160))
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 80))
        achievements = self.game.save.data.get("achievements", {})
        for idx, achievement in enumerate(ACHIEVEMENTS.values()):
            unlocked = achievements.get(achievement.id, False)
            color = (200, 240, 200) if unlocked else (120, 120, 120)
            text = self.font.render(f"{achievement.name} - {achievement.description}", True, color)
            surface.blit(text, (80, 180 + idx * 40))


class StageSelectState(Scene):
    def __init__(self, game) -> None:
        self.game = game
        self.font = game.fonts.get("arial", 28)
        self.title_font = game.fonts.get("arial", 48)
        self.stages = self._load_stage_list()
        self.selected_zone = "City"
        self.selected_stage_index = 0

    def _load_stage_list(self) -> Dict[str, List[dict]]:
        data_path = self.game.base_path / "data" / "stages.json"
        if data_path.exists():
            return json.loads(data_path.read_text())
        return {"City": []}

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.game.open_main_menu()
            elif event.key == pygame.K_TAB:
                zones = list(self.stages.keys())
                idx = zones.index(self.selected_zone)
                self.selected_zone = zones[(idx + 1) % len(zones)]
                self.selected_stage_index = 0
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_stage_index = min(self.selected_stage_index + 1, len(self.stages[self.selected_zone]) - 1)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected_stage_index = max(self.selected_stage_index - 1, 0)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_selected_stage()

    def _start_selected_stage(self) -> None:
        zone_stages = self.stages.get(self.selected_zone, [])
        if zone_stages:
            stage = zone_stages[self.selected_stage_index]
            self.game.open_stage(stage["id"])

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        surface.fill((18, 20, 30))
        title = self.title_font.render(f"{self.selected_zone} Stages", True, (255, 220, 160))
        surface.blit(title, (60, 80))
        zone_stages = self.stages.get(self.selected_zone, [])
        completed = self.game.save.get_completed_stages()
        for idx, stage in enumerate(zone_stages):
            color = (255, 255, 255) if idx == self.selected_stage_index else (160, 160, 180)
            entry = self.font.render(f"{stage['name']} ({stage['id']})", True, color)
            surface.blit(entry, (80, 180 + idx * 36))
            result = completed.get(stage["id"])
            if result:
                stars = "★" * result.get("stars", 0)
                star_text = self.font.render(stars, True, (255, 220, 80))
                surface.blit(star_text, (480, 180 + idx * 36))


class PauseState(Scene):
    def __init__(self, game, stage_state) -> None:
        self.game = game
        self.stage_state = stage_state
        self.font = game.fonts.get("arial", 42)
        self.options = ["Resume", "Restart", "Stage Select", "Settings"]
        self.selection = 0

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.game.scene_manager.pop()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selection = (self.selection + 1) % len(self.options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selection = (self.selection - 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate()

    def _activate(self) -> None:
        option = self.options[self.selection]
        if option == "Resume":
            self.game.scene_manager.pop()
        elif option == "Restart":
            self.game.open_stage(self.stage_state.stage_id)
        elif option == "Stage Select":
            self.game.open_stage_select()
        elif option == "Settings":
            self.game.scene_manager.push(SettingsState(self.game))

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        self.stage_state.draw(surface)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        for idx, option in enumerate(self.options):
            color = (255, 255, 255) if idx == self.selection else (150, 150, 150)
            text = self.font.render(option, True, color)
            surface.blit(text, (surface.get_width() // 2 - text.get_width() // 2, 260 + idx * 60))


class StageState(Scene):
    def __init__(self, game, stage_id: str) -> None:
        self.game = game
        self.stage_id = stage_id
        stage_path = self._resolve_stage_path(stage_id)
        self.script = StageScript.from_json(stage_path)
        self.hud = HUD(game.fonts)
        self.particles = ParticleSystem()
        self.player = Player((240, 620), self.hud, self.particles)
        self.ground_y = 620
        self.enemies: List[Enemy] = []
        self.hostages: List[Hostage] = []
        self.powerups: List[Powerup] = []
        self.objects: List = []
        self.boss: Optional[Boss] = None
        self.bombs: List[dict] = []
        self.score = 0
        self.coins_earned = 0
        self.stage_time = 0.0
        self.completed = False
        self.failed = False
        self.background_layers = self._create_parallax(self.script.zone)
        self.camera = self.game.camera
        self.camera.position.x = 0
        self.camera.set_target(0)
        self.spawner = Spawner(self.script, {
            "spawn": self._handle_spawn,
            "powerup": self._handle_powerup,
            "hostage": self._handle_hostage,
            "barrel": self._handle_barrel,
            "crate": self._handle_crate,
            "boss": self._handle_boss,
            "camera_pan": self._handle_camera_pan,
        })
        self.stats = {
            "shots_fired": 0,
            "hits": 0,
            "hostages_saved": 0,
            "hostages_lost": 0,
            "damage_taken": 0,
            "best_combo": 0,
            "barrel_multi_kill": 0,
        }
        self.combo_text_timer = 0.0
        self.music_started = False

    def _resolve_stage_path(self, stage_id: str) -> Path:
        return self.game.base_path / "data" / f"{stage_id}.json"

    def _create_parallax(self, zone: str) -> List[pygame.Surface]:
        width, height = self.game.display.get_size()
        layers = []
        colors = {
            "City": [(20, 20, 28), (30, 40, 60), (60, 80, 110), (120, 140, 170)],
            "Jungle": [(16, 30, 20), (24, 60, 40), (40, 100, 60), (80, 140, 80)],
            "Desert": [(26, 22, 16), (60, 50, 32), (120, 90, 50), (200, 170, 90)],
        }
        palette = colors.get(zone, colors["City"])
        for idx, color in enumerate(palette):
            layer = pygame.Surface((width * 2, height))
            layer.fill(color)
            pygame.draw.rect(layer, tuple(min(255, c + 20) for c in color), (0, height - (idx + 1) * 80, layer.get_width(), (idx + 1) * 80))
            layers.append(layer)
        return layers

    def enter(self) -> None:
        self.game.audio.play_music(self.script.music, loop=True)

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.scene_manager.push(PauseState(self.game, self))
            elif event.key == pygame.K_r:
                self.player.reload()
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                weapons = list(WEAPON_DATA.keys())
                idx = event.key - pygame.K_1
                if idx < len(weapons) and self.game.save.get_weapon_unlocks().get(weapons[idx], False):
                    self.player.switch_weapon(weapons[idx])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == BUTTON_RIGHT:
            if not self.player.is_ducking():
                self.player.begin_duck()
                self.register_duck()

    def update(self, dt: float) -> None:
        if self.failed or self.completed:
            return
        self.stage_time += dt
        self.player.update(dt, self)
        self.particles.update(dt)
        self.spawner.update(dt)
        self._update_lists(dt)
        self.camera.update(dt)
        self.hud.update(dt)
        self._update_bombs(dt)
        input_manager = self.game.input
        if input_manager.was_pressed(BUTTON_LEFT):
            self.player.shoot(self)
        if input_manager.was_pressed(pygame.K_SPACE):
            if not self.player.is_ducking():
                self.player.begin_duck()
                self.register_duck()
        if self.stage_time >= self.script.duration and not self.enemies and not self.boss:
            self.complete_stage()

    def _update_lists(self, dt: float) -> None:
        time_scale = 0.6 if self.player.powerups.get("slow", 0) > 0 else 1.0
        for collection in (self.enemies, self.hostages, self.objects):
            for actor in list(collection):
                actor.update(dt * time_scale, self)
                if not actor.alive:
                    collection.remove(actor)
        for powerup in list(self.powerups):
            powerup.update(dt, self)
            if self.player.rect.colliderect(powerup.rect):
                self._collect_powerup(powerup)
                self.powerups.remove(powerup)
            elif not powerup.alive:
                self.powerups.remove(powerup)
        if self.boss:
            if self.boss.alive:
                self.boss.update(dt, self)
            else:
                self.boss = None

    def _update_bombs(self, dt: float) -> None:
        for bomb in list(self.bombs):
            bomb["timer"] -= dt
            if bomb["timer"] <= 0:
                self.spawn_hit_spark(bomb["position"])
                if not self.player.is_ducking():
                    self.damage_player(1)
                self.bombs.remove(bomb)

    def draw(self, surface) -> None:
        surface.fill((0, 0, 0))
        self._draw_background(surface)
        for obj in self.objects:
            obj.draw(surface, self.camera)
        for hostage in self.hostages:
            hostage.draw(surface, self.camera)
        for enemy in self.enemies:
            enemy.draw(surface, self.camera)
        if self.boss:
            self.boss.draw(surface, self.camera)
        for powerup in self.powerups:
            powerup.draw(surface, self.camera)
        self.player.draw(surface, self.camera)
        self.particles.draw(surface, self.camera)
        self.hud.draw(surface, self)

    def _draw_background(self, surface) -> None:
        for idx, layer in enumerate(self.background_layers):
            offset = int(self.camera.position.x * (0.1 * idx))
            x = -offset % layer.get_width()
            surface.blit(layer, (x - layer.get_width(), 0))
            surface.blit(layer, (x, 0))

    # Spawn handlers -----------------------------------------------------
    def _handle_spawn(self, event) -> None:
        enemy_type = event.params.get("type", "grunt")
        x = event.params.get("x", 900)
        y = event.params.get("y", self.ground_y)
        factory = ENEMY_FACTORIES.get(enemy_type)
        if factory:
            enemy = factory((x, y))
            self.enemies.append(enemy)

    def _handle_powerup(self, event) -> None:
        x = event.params.get("x", 900)
        y = event.params.get("y", self.ground_y - 60)
        ptype = event.params.get("kind", "rapid")
        duration = event.params.get("duration", 6.0)
        self.powerups.append(Powerup((x, y), ptype, duration))

    def _handle_hostage(self, event) -> None:
        x = event.params.get("x", 900)
        y = event.params.get("y", self.ground_y)
        hostage = Hostage((x, y))
        self.hostages.append(hostage)

    def _handle_barrel(self, event) -> None:
        x = event.params.get("x", 900)
        y = event.params.get("y", self.ground_y)
        barrel = ExplosiveBarrel((x, y))
        self.objects.append(barrel)

    def _handle_crate(self, event) -> None:
        x = event.params.get("x", 900)
        y = event.params.get("y", self.ground_y)
        crate = CoinCrate((x, y), coins=event.params.get("coins", 10))
        self.objects.append(crate)

    def _handle_boss(self, event) -> None:
        phases = [
            BossPhase(threshold=0.9, weak_spots=[pygame.Rect(60, 40, 40, 40)], attack_interval=2.5),
            BossPhase(threshold=0.6, weak_spots=[pygame.Rect(80, 20, 60, 60)], attack_interval=2.0),
            BossPhase(threshold=0.3, weak_spots=[pygame.Rect(40, 80, 80, 40)], attack_interval=1.6),
        ]
        self.boss = Boss((self.camera.position.x + 900, self.ground_y), max_health=600, phases=phases)

    def _handle_camera_pan(self, event) -> None:
        target = event.params.get("target_x", self.camera.position.x + 200)
        self.camera.set_target(target)

    # Gameplay events ----------------------------------------------------
    def get_shoot_targets(self):
        targets = []
        targets.extend(self.enemies)
        targets.extend(self.hostages)
        targets.extend(self.objects)
        if self.boss:
            targets.append(self.boss)
        return targets

    def register_hit(self, headshot: bool = False) -> None:
        self.stats["shots_fired"] += 1
        self.stats["hits"] += 1
        self.player.combo_hits += 1
        self.player.combo_decay = 2.0
        self.player.combo_multiplier = clamp(1.0 + self.player.combo_hits / 5, 1.0, 5.0)
        self.stats["best_combo"] = max(self.stats["best_combo"], self.player.combo_hits)
        bonus = 100 * self.player.combo_multiplier
        if headshot:
            bonus += 50
            self.hud.add_message("Bullseye!", (255, 240, 150))
        self.score += int(bonus)
        self.hud.set_combo(f"x{self.player.combo_multiplier:.1f}")

    def register_miss(self) -> None:
        self.stats["shots_fired"] += 1
        self.player.combo_hits = 0
        self.player.combo_multiplier = 1.0
        self.player.combo_decay = 0.0

    def register_duck(self) -> None:
        self.player.combo_hits = 0
        self.player.combo_multiplier = 1.0
        self.player.combo_decay = 0.0

    def on_enemy_killed(self, enemy: Enemy) -> None:
        self.score += int(200 * self.player.combo_multiplier)
        self.coins_earned += 5
        self.hud.add_message("Enemy down", (200, 220, 255))

    def on_hostage_hit(self, hostage: Hostage) -> None:
        self.stats["hostages_lost"] += 1
        self.score -= 200
        self.hud.add_message("Civilian hit!", (255, 80, 80))
        self.register_miss()

    def on_hostage_rescued(self, hostage: Hostage) -> None:
        self.stats["hostages_saved"] += 1
        self.score += 250
        self.player.heal(1)
        self.hud.add_message("Hostage rescued", (120, 255, 160))

    def on_barrel_exploded(self, barrel) -> None:
        self.hud.add_message("Kaboom!", (255, 200, 80))
        kills = 0
        for enemy in list(self.enemies):
            if enemy.rect.centerx in range(barrel.rect.centerx - 120, barrel.rect.centerx + 120):
                enemy.take_damage(200, self)
                if not enemy.alive:
                    kills += 1
        self.stats["barrel_multi_kill"] = max(self.stats["barrel_multi_kill"], kills)
        self.spawn_hit_spark(barrel.rect.center)

    def on_coin_crate_broken(self, crate) -> None:
        self.coins_earned += crate.coins
        self.score += crate.coins * 10
        self.hud.add_message(f"+{crate.coins} coins", (255, 220, 140))

    def spawn_hit_spark(self, position) -> None:
        self.particles.spawn(pygame.Vector2(position), pygame.Vector2(0, 0), 0.2, (255, 200, 120), 6)

    def spawn_bomb(self, position) -> None:
        self.bombs.append({"position": pygame.Vector2(position), "timer": 1.2})

    def _collect_powerup(self, powerup: Powerup) -> None:
        if powerup.type == "health":
            self.player.heal(2)
            self.hud.add_message("Health up", (120, 255, 160))
        elif powerup.type == "armor":
            self.player.apply_powerup("armor", powerup.duration)
            self.hud.add_message("Armor", (200, 220, 255))
        elif powerup.type == "slow":
            self.player.apply_powerup("slow", powerup.duration)
            self.hud.add_message("Slow-mo", (180, 200, 255))
        elif powerup.type == "spread":
            self.player.apply_powerup("spread", powerup.duration)
            self.hud.add_message("Spread Shot", (255, 220, 180))
        else:
            self.player.apply_powerup(powerup.type, powerup.duration)
            self.hud.add_message(powerup.type.title(), (200, 220, 255))

    def damage_player(self, amount: int) -> None:
        self.player.take_damage(amount, self)
        self.stats["damage_taken"] += amount

    def on_player_hit(self) -> None:
        self.register_duck()

    def on_boss_defeated(self, boss: Boss) -> None:
        self.score += 2000
        self.complete_stage()

    def fail_stage(self) -> None:
        if not self.failed:
            self.failed = True
            self.game.scene_manager.replace(StageClearState(self.game, self, success=False))

    def complete_stage(self) -> None:
        if not self.completed:
            self.completed = True
            stats = self._compile_stats()
            evaluate_achievements(self.game.save, stats)
            stars = self._calculate_stars(stats)
            self.game.save.set_stage_result(self.stage_id, stars, self.score)
            self.game.save.add_coins(self.coins_earned)
            self.game.scene_manager.replace(StageClearState(self.game, self, success=True, stats=stats, stars=stars))

    def _compile_stats(self) -> dict:
        accuracy = 0.0
        if self.stats["shots_fired"]:
            accuracy = self.stats["hits"] / self.stats["shots_fired"]
        return {
            **self.stats,
            "accuracy": accuracy,
            "score": self.score,
            "time": self.stage_time,
        }

    def _calculate_stars(self, stats: dict) -> int:
        stars = 1
        if stats["accuracy"] >= 0.7 and stats["hostages_lost"] == 0:
            stars += 1
        if stats["time"] <= self.script.duration * 0.9 and stats["damage_taken"] <= 1:
            stars += 1
        return int(clamp(stars, 1, 3))


class StageClearState(Scene):
    def __init__(self, game, stage_state: StageState, success: bool, stats: Optional[dict] = None, stars: int = 0) -> None:
        self.game = game
        self.stage_state = stage_state
        self.success = success
        self.stats = stats or {}
        self.stars = stars
        self.font_title = game.fonts.get("arial", 54)
        self.font = game.fonts.get("arial", 28)

    def handle_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.game.open_stage_select()
            elif event.key == pygame.K_r and self.success:
                self.game.open_stage(self.stage_state.stage_id)
            elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.game.open_main_menu()

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface) -> None:
        surface.fill((18, 20, 26))
        title_text = "Stage Clear" if self.success else "Mission Failed"
        title = self.font_title.render(title_text, True, (255, 220, 160))
        surface.blit(title, (surface.get_width() // 2 - title.get_width() // 2, 120))
        if self.success:
            stars = "★" * self.stars
            star_surface = self.font.render(stars, True, (255, 220, 80))
            surface.blit(star_surface, (surface.get_width() // 2 - star_surface.get_width() // 2, 200))
            lines = [
                f"Score: {self.stage_state.score}",
                f"Accuracy: {self.stats.get('accuracy', 0.0)*100:.1f}%",
                f"Time: {self.stats.get('time', 0):.1f}s",
                f"Hostages saved: {self.stats.get('hostages_saved', 0)}",
            ]
            for idx, line in enumerate(lines):
                text = self.font.render(line, True, (220, 220, 220))
                surface.blit(text, (surface.get_width() // 2 - text.get_width() // 2, 280 + idx * 40))
        else:
            text = self.font.render("Press Enter to retry", True, (220, 220, 220))
            surface.blit(text, (surface.get_width() // 2 - text.get_width() // 2, 260))
