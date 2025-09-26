"""Entry point for Railshot Heroes."""
from __future__ import annotations

from pathlib import Path

from core.game import Game


def main() -> None:
    base_path = Path(__file__).parent
    game = Game(base_path)
    # Register placeholder audio tracks to avoid missing lookups.
    game.audio.load_music("menu", "menu_theme.ogg")
    game.audio.load_music("city_theme.ogg", "city_theme.ogg")
    game.audio.load_music("jungle_theme.ogg", "jungle_theme.ogg")
    game.audio.load_music("desert_theme.ogg", "desert_theme.ogg")
    game.start()


if __name__ == "__main__":
    main()
