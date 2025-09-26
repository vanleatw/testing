"""Enemy hierarchy with simple behaviours."""
from __future__ import annotations

import pygame

from actors.base import Actor


class Enemy(Actor):
    def __init__(self, position, health: int, color: tuple[int, int, int]) -> None:
        super().__init__(position)
        self.health = health
        self.color = color
        self.head_rect = pygame.Rect(0, 0, self.rect.width // 2, self.rect.height // 3)
        self.head_rect.midbottom = self.rect.midtop
        self.cover = None
        self.attack_timer = 2.0

    def update(self, dt: float, stage_state) -> None:
        super().update(dt, stage_state)
        self.head_rect.midbottom = self.rect.midtop
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.perform_attack(stage_state)

    def perform_attack(self, stage_state) -> None:
        stage_state.player.take_damage(1, stage_state)
        self.attack_timer = 2.5
        stage_state.hud.add_message("Hit!", (255, 100, 120))

    def take_damage(self, amount: float, stage_state, headshot: bool = False) -> None:
        if headshot:
            amount *= 2
        self.health -= amount
        stage_state.spawn_hit_spark(self.rect.center)
        if self.health <= 0:
            self.alive = False
            stage_state.on_enemy_killed(self)

    def draw(self, surface: pygame.Surface, camera) -> None:  # pragma: no cover
        rect = camera.apply(self.rect)
        pygame.draw.rect(surface, self.color, rect, border_radius=8)
        head = self.head_rect.copy()
        head = camera.apply(head)
        pygame.draw.ellipse(surface, (220, 210, 190), head)


class ShieldEnemy(Enemy):
    def __init__(self, position) -> None:
        super().__init__(position, health=80, color=(200, 160, 80))
        self.shield_health = 50

    def take_damage(self, amount: float, stage_state, headshot: bool = False) -> None:
        if self.shield_health > 0 and not headshot:
            self.shield_health -= amount
            stage_state.spawn_hit_spark((self.rect.centerx - 20, self.rect.centery))
            if self.shield_health <= 0:
                stage_state.hud.add_message("Shield Broken!", (255, 200, 80))
        else:
            super().take_damage(amount, stage_state, headshot)

    def draw(self, surface, camera) -> None:  # pragma: no cover
        super().draw(surface, camera)
        rect = camera.apply(self.rect)
        shield_rect = rect.inflate(20, 10)
        pygame.draw.rect(surface, (80, 160, 220), shield_rect, width=4, border_radius=12)


class SniperEnemy(Enemy):
    def __init__(self, position) -> None:
        super().__init__(position, health=50, color=(200, 80, 80))
        self.charge_time = 3.0
        self.laser_color = (255, 50, 50)

    def update(self, dt: float, stage_state) -> None:
        super().update(dt, stage_state)
        self.charge_time -= dt
        if self.charge_time <= 0:
            stage_state.player.take_damage(2, stage_state)
            stage_state.hud.add_message("Sniper Shot!", (255, 120, 120))
            self.charge_time = 3.5

    def draw(self, surface, camera) -> None:  # pragma: no cover
        super().draw(surface, camera)
        start = camera.world_to_screen(pygame.Vector2(self.rect.centerx, self.rect.centery))
        end = start + pygame.Vector2(1000, -100)
        pygame.draw.line(surface, self.laser_color, start, end, 2)


class BomberEnemy(Enemy):
    def __init__(self, position) -> None:
        super().__init__(position, health=60, color=(200, 120, 40))
        self.throw_timer = 2.5

    def update(self, dt: float, stage_state) -> None:
        super().update(dt, stage_state)
        self.throw_timer -= dt
        if self.throw_timer <= 0:
            stage_state.spawn_bomb(self.rect.center)
            self.throw_timer = 3.0


class TurretEnemy(Enemy):
    def __init__(self, position) -> None:
        super().__init__(position, health=120, color=(150, 150, 150))
        self.attack_timer = 1.2

    def perform_attack(self, stage_state) -> None:
        stage_state.player.take_damage(1, stage_state)
        self.attack_timer = 1.2

    def draw(self, surface, camera) -> None:  # pragma: no cover
        rect = camera.apply(self.rect)
        pygame.draw.rect(surface, (120, 120, 120), rect)
        barrel = pygame.Rect(rect.centerx, rect.centery - 10, 40, 20)
        pygame.draw.rect(surface, (180, 180, 180), barrel)


class MeleeEnemy(Enemy):
    def __init__(self, position) -> None:
        super().__init__(position, health=40, color=(160, 200, 120))
        self.speed = 80

    def update(self, dt: float, stage_state) -> None:
        direction = pygame.Vector2(stage_state.player.rect.center) - self.position
        if direction.length() > 5:
            self.position += direction.normalize() * self.speed * dt
        super().update(dt, stage_state)


ENEMY_FACTORIES = {
    "grunt": lambda pos: Enemy(pos, health=60, color=(160, 80, 80)),
    "shield": lambda pos: ShieldEnemy(pos),
    "sniper": lambda pos: SniperEnemy(pos),
    "bomber": lambda pos: BomberEnemy(pos),
    "turret": lambda pos: TurretEnemy(pos),
    "melee": lambda pos: MeleeEnemy(pos),
}
