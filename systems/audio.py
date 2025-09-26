"""Simple wrapper around pygame's audio playback."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pygame


class AudioSystem:
    """Loads and plays short sound effects and music."""

    def __init__(self, assets_path: Path) -> None:
        self.assets_path = assets_path
        self.sfx: Dict[str, pygame.mixer.Sound] = {}
        self.music_tracks: Dict[str, Path] = {}
        self.master_volume = 0.7
        self.music_volume = 0.5

    def load_sfx(self, name: str, filename: str) -> None:
        path = self.assets_path / "sfx" / filename
        if path.exists():
            self.sfx[name] = pygame.mixer.Sound(str(path))
            self.sfx[name].set_volume(self.master_volume)

    def play_sfx(self, name: str) -> None:
        sound = self.sfx.get(name)
        if sound:
            sound.set_volume(self.master_volume)
            sound.play()

    def load_music(self, name: str, filename: str) -> None:
        self.music_tracks[name] = self.assets_path / "music" / filename

    def play_music(self, name: str, loop: bool = True) -> None:
        track = self.music_tracks.get(name)
        if track and track.exists():
            pygame.mixer.music.load(str(track))
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1 if loop else 0)

    def stop_music(self) -> None:
        pygame.mixer.music.stop()

    def set_master_volume(self, volume: float) -> None:
        self.master_volume = volume
        for sound in self.sfx.values():
            sound.set_volume(volume)

    def set_music_volume(self, volume: float) -> None:
        self.music_volume = volume
        pygame.mixer.music.set_volume(volume)
