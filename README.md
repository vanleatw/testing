# Railshot Heroes

Railshot Heroes is a polished, replayable on-rails tap shooter inspired by *Major Mayhem*. It is built with Python and `pygame` and showcases a state-driven architecture with JSON-scripted stages, unlockable weapons, achievements, and a lightweight shop.

## Getting started

1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Run the game**
   ```bash
   python main.py
   ```

The window is resizable and defaults to a 1280×720 letterboxed presentation. The first launch creates a JSON save file under `data/save.json`.

## Controls

| Action | Input |
| ------ | ----- |
| Shoot | Left mouse button |
| Duck behind cover | Right mouse button or `Space` |
| Reload | `R` |
| Switch weapons | `1`–`4` |
| Pause | `Esc` |
| Menu navigation | Arrow keys / `WASD`, `Enter`, `Space`, `Esc` |

## Project structure

```
core/        – game loop, camera, input, timer, scene manager
actors/      – player, enemies, bosses, hostages, powerups, interactive props
systems/     – stage scripting, spawning, particles, UI/HUD, audio, shop, achievements
utils/       – math helpers, easing/tween utilities, rectangle helpers
assets/      – placeholder folders for sprites, audio, fonts, and stage art
data/        – stage JSON files, weapon definitions, upgrades, save data
tests/       – lightweight tests for the stage parser and save system
```

All art is generated procedurally using simple vector-style primitives so bespoke assets can be dropped into the `assets/` directory later without modifying code.

## Adding a new stage

1. Create a JSON file under `data/` named `stage_<zone>_<number>.json`.
2. Populate it with the stage metadata and a `timeline` array. Each entry requires `time`, `action`, and optional `params`. Example:
   ```json
   {
     "id": "stage_city_11",
     "zone": "City",
     "background": "city",
     "music": "city_theme.ogg",
     "timeline": [
       {"time": 2.0, "action": "spawn", "params": {"type": "grunt", "x": 900, "y": 620}},
       {"time": 4.0, "action": "hostage", "params": {"x": 960, "y": 620}},
       {"time": 5.5, "action": "powerup", "params": {"kind": "spread", "duration": 6.0}}
     ],
     "duration": 20.0
   }
   ```
3. Register the stage inside `data/stages.json` under the appropriate zone. The entry should include a user-facing `name` and the stage `id`.
4. Launch the game and select the stage from the stage-select menu.

Supported timeline actions include:

- `spawn`: Spawn an enemy (`type` must match keys in `ENEMY_FACTORIES`).
- `hostage`: Drop a civilian to rescue.
- `powerup`: Spawn a timed powerup (`kind` may be `rapid`, `spread`, `armor`, `slow`, or `health`).
- `barrel` / `crate`: Spawn explosive barrels or coin crates.
- `boss`: Trigger a zone boss.
- `camera_pan`: Smoothly pan the camera to a new x-coordinate.

## Testing

Run the lightweight unit tests to validate stage parsing and save/load round-trips:

```bash
pytest
```

## License

This project ships with placeholder content for demonstration purposes only. Replace `assets/` with your own art, audio, and fonts before publishing.
