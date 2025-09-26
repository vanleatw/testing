"""Player actor handling shooting, ducking and powerups."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pygame

from actors.base import Actor
from actors.hostage import Hostage
from systems.collision import hitscan
from systems.particles import ParticleSystem


@dataclass
class WeaponStats:
    id: str
    damage: int
    mag_size: int
    reload_time: float
    rof: float
    spread: float


WEAPON_DATA: Dict[str, WeaponStats] = {
    "pistol": WeaponStats("pistol", damage=25, mag_size=12, reload_time=1.0, rof=0.2, spread=2.0),
    "smg": WeaponStats("smg", damage=18, mag_size=32, reload_time=1.1, rof=0.08, spread=4.0),
    "shotgun": WeaponStats("shotgun", damage=12, mag_size=8, reload_time=1.3, rof=0.5, spread=10.0),
    "carbine": WeaponStats("carbine", damage=35, mag_size=20, reload_time=1.4, rof=0.15, spread=1.5),
}


class Player(Actor):
    def __init__(self, position, hud, particles: ParticleSystem) -> None:
        super().__init__(position)
        self.rect.size = (80, 120)
        self.rect.midbottom = position
        self.health = 5
        self.max_health = 5
        self.weapon_id = "pistol"
        self.weapon = WEAPON_DATA[self.weapon_id]
        self.ammo = self.weapon.mag_size
        self.reload_timer = 0.0
        self.shoot_timer = 0.0
        self.duck_timer = 0.0
        self.duck_duration = 0.6
        self.particles = particles
        self.hud = hud
        self.combo_hits = 0
        self.combo_multiplier = 1.0
        self.combo_decay = 0.0
        self.invulnerable = False
        self.powerups: Dict[str, float] = {}

    def update(self, dt: float, stage_state) -> None:
        super().update(dt, stage_state)
        self.rect.midbottom = (self.rect.midbottom[0], stage_state.ground_y)
        self.combo_decay = max(0.0, self.combo_decay - dt)
        if self.combo_decay == 0:
            self.combo_hits = 0
            self.combo_multiplier = 1.0
        self.reload_timer = max(0.0, self.reload_timer - dt)
        self.shoot_timer = max(0.0, self.shoot_timer - dt)
        if self.duck_timer > 0:
            self.duck_timer -= dt
            if self.duck_timer <= 0:
                self.invulnerable = False
        for key in list(self.powerups.keys()):
            self.powerups[key] = max(0.0, self.powerups[key] - dt)
            if self.powerups[key] == 0:
                self.powerups.pop(key)
                if key == "armor":
                    self.invulnerable = False
        for name, time_left in self.powerups.items():
            self.hud.set_powerup_timer(name, time_left)

    def begin_duck(self) -> None:
        self.duck_timer = self.duck_duration
        self.invulnerable = True
        self.hud.add_message("Cover!")

    def is_ducking(self) -> bool:
        return self.duck_timer > 0

    def can_shoot(self) -> bool:
        return not self.is_ducking() and self.reload_timer == 0 and self.shoot_timer == 0 and self.ammo > 0

    def shoot(self, stage_state) -> None:
        if not self.can_shoot():
            return
        self.ammo -= 1
        rof = self.weapon.rof
        if "rapid" in self.powerups:
            rof *= 0.5
        self.shoot_timer = rof
        cursor_world = stage_state.camera.screen_to_world(pygame.mouse.get_pos())
        target = hitscan(cursor_world, stage_state.get_shoot_targets())
        muzzle_pos = pygame.Vector2(self.rect.centerx, self.rect.top + 20)
        self.particles.spawn(muzzle_pos, pygame.Vector2(0, -20), 0.1, (255, 200, 100), 8)
        headshot = False
        if target:
            if isinstance(target, Hostage):
                if target.rope_rect.collidepoint(cursor_world):
                    target.rescue(stage_state)
                    stage_state.register_hit()
                    return
            if hasattr(target, "head_rect"):
                headshot = target.head_rect.collidepoint(cursor_world)
            target.take_damage(self.get_damage(), stage_state, headshot=headshot)
            if "spread" in self.powerups:
                for extra in stage_state.enemies:
                    if extra is target:
                        continue
                    if extra.rect.centerx in range(target.rect.centerx - 120, target.rect.centerx + 120):
                        extra.take_damage(self.weapon.damage * 0.6, stage_state)
            stage_state.register_hit(headshot=headshot)
        else:
            stage_state.register_miss()
        if self.ammo <= 0:
            self.reload()

    def reload(self) -> None:
        if self.reload_timer == 0 and self.ammo < self.weapon.mag_size:
            reload_time = self.weapon.reload_time
            if "reload" in self.powerups:
                reload_time *= 0.7
            self.reload_timer = reload_time
            self.hud.add_message("Reloading", (180, 220, 255))

    def update_reload(self, dt: float) -> None:
        if self.reload_timer > 0:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                self.ammo = self.weapon.mag_size

    def take_damage(self, amount: float, stage_state, headshot: bool = False) -> None:
        if self.invulnerable or self.powerups.get("armor", 0) > 0:
            amount *= 0.5
        if self.invulnerable and self.powerups.get("armor", 0) <= 0:
            return
        self.health -= amount
        stage_state.on_player_hit()
        if self.health <= 0:
            stage_state.fail_stage()

    def heal(self, amount: int = 1) -> None:
        self.health = min(self.max_health, self.health + amount)

    def apply_powerup(self, name: str, duration: float) -> None:
        self.powerups[name] = duration

    def get_damage(self) -> float:
        damage = self.weapon.damage
        if "armor_pierce" in self.powerups:
            damage *= 1.5
        return damage

    def switch_weapon(self, weapon_id: str) -> None:
        if weapon_id in WEAPON_DATA:
            self.weapon_id = weapon_id
            self.weapon = WEAPON_DATA[weapon_id]
            self.ammo = self.weapon.mag_size
            self.reload_timer = 0
            self.hud.add_message(f"Equipped {weapon_id.title()}", (200, 200, 255))

    def draw(self, surface: pygame.Surface, camera) -> None:  # pragma: no cover - drawing
        body_color = (60, 120, 180)
        if self.is_ducking():
            body_color = (40, 80, 120)
        rect = camera.apply(self.rect)
        pygame.draw.rect(surface, body_color, rect, border_radius=12)
        if not self.is_ducking():
            head_rect = pygame.Rect(0, 0, rect.width // 2, rect.height // 3)
            head_rect.midbottom = rect.midtop
            pygame.draw.ellipse(surface, (240, 220, 180), head_rect)
