"""Basic particle system for hit sparks and muzzle flashes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pygame


@dataclass
class Particle:
    position: pygame.Vector2
    velocity: pygame.Vector2
    lifetime: float
    color: tuple[int, int, int]
    radius: float


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: List[Particle] = []

    def spawn(self, position: pygame.Vector2, velocity: pygame.Vector2, lifetime: float, color, radius: float) -> None:
        self.particles.append(Particle(position, velocity, lifetime, color, radius))

    def update(self, dt: float) -> None:
        for particle in list(self.particles):
            particle.lifetime -= dt
            if particle.lifetime <= 0:
                self.particles.remove(particle)
                continue
            particle.position += particle.velocity * dt

    def draw(self, surface: pygame.Surface, camera) -> None:
        for particle in self.particles:
            pos = camera.world_to_screen(particle.position)
            pygame.draw.circle(surface, particle.color, (int(pos.x), int(pos.y)), int(max(1, particle.radius)))
