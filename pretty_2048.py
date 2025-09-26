
"""A colorful, animated 2048 clone rendered in a standalone Tkinter window."""
from __future__ import annotations

import random
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

BOARD_SIZE = 4
WIN_TILE = 2048
GRID_PADDING = 20
TILE_SIZE = 100
TILE_GAP = 12
ANIMATION_STEPS = 10
ANIMATION_DELAY_MS = 15
NEW_TILE_ANIMATION_STEPS = 6
NEW_TILE_DELAY_MS = 20


TILE_COLORS: Dict[int, Tuple[str, str]] = {
    0: ("#cdc1b4", "#776e65"),
    2: ("#eee4da", "#776e65"),
    4: ("#ede0c8", "#776e65"),
    8: ("#f2b179", "#f9f6f2"),
    16: ("#f59563", "#f9f6f2"),
    32: ("#f67c5f", "#f9f6f2"),
    64: ("#f65e3b", "#f9f6f2"),
    128: ("#edcf72", "#f9f6f2"),
    256: ("#edcc61", "#f9f6f2"),
    512: ("#edc850", "#f9f6f2"),
    1024: ("#edc53f", "#f9f6f2"),
    2048: ("#edc22e", "#f9f6f2"),
}

BEYOND_COLOR = ("#3c3a32", "#f9f6f2")
BACKGROUND_COLOR = "#bbada0"
BOARD_BACKGROUND = "#cdc1b4"


@dataclass
class TileWidget:
    tile_id: int
    value: int
    row: int
    col: int
    canvas: tk.Canvas
    font_map: Dict[str, tkfont.Font]

    def __post_init__(self) -> None:
        self.rect = self.canvas.create_rectangle(0, 0, 0, 0, width=0, tags=("tile", f"tile-{self.tile_id}"))
        self.text = self.canvas.create_text(0, 0, tags=("tile-text", f"tile-text-{self.tile_id}"))
        self.update_position(self.row, self.col)
        self.update_style()

    def grid_to_pixel(self, row: int, col: int) -> Tuple[float, float]:
        x = GRID_PADDING + col * (TILE_SIZE + TILE_GAP)
        y = GRID_PADDING + row * (TILE_SIZE + TILE_GAP)
        return x, y

    def update_position(self, row: int, col: int) -> None:
        self.row = row
        self.col = col
        x, y = self.grid_to_pixel(row, col)
        self.canvas.coords(self.rect, x, y, x + TILE_SIZE, y + TILE_SIZE)
        self.canvas.coords(self.text, x + TILE_SIZE / 2, y + TILE_SIZE / 2)

    def move_by(self, dx: float, dy: float) -> None:
        self.canvas.move(self.rect, dx, dy)
        self.canvas.move(self.text, dx, dy)

    def update_style(self) -> None:
        fg_bg = TILE_COLORS.get(self.value, BEYOND_COLOR)
        bg_color, fg_color = fg_bg
        self.canvas.itemconfigure(self.rect, fill=bg_color)
        font = self._font_for_value(self.value)
        self.canvas.itemconfigure(self.text, text=str(self.value), fill=fg_color, font=font)

    def set_value(self, value: int) -> None:
        self.value = value
        self.update_style()

    def _font_for_value(self, value: int) -> tkfont.Font:
        digits = len(str(value))
        if digits <= 2:
            return self.font_map["large"]
        if digits == 3:
            return self.font_map["medium"]
        return self.font_map["small"]

    def destroy(self) -> None:
        self.canvas.delete(self.rect)
        self.canvas.delete(self.text)


class Game2048App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("2048 - Vibrant Edition")
        self.root.resizable(False, False)

        width = GRID_PADDING * 2 + BOARD_SIZE * TILE_SIZE + (BOARD_SIZE - 1) * TILE_GAP
        height = width + 120
        self.root.geometry(f"{width}x{height}")

        self.header = tk.Frame(root, bg=BACKGROUND_COLOR)
        self.header.pack(fill=tk.X)

        self.title_label = tk.Label(
            self.header,
            text="2048",
            font=tkfont.Font(size=28, weight="bold"),
            bg=BACKGROUND_COLOR,
            fg="#f9f6f2",
        )
        self.title_label.pack(side=tk.LEFT, padx=20, pady=10)

        self.score_var = tk.StringVar()
        self.best_var = tk.StringVar()
        self.score_box = self._build_score_box("SCORE", self.score_var)
        self.best_box = self._build_score_box("BEST", self.best_var)
        self.best_box.pack(side=tk.RIGHT, padx=20)
        self.score_box.pack(side=tk.RIGHT, padx=10)

        self.message_var = tk.StringVar(value="Use arrow keys or WASD to play")
        self.message_label = tk.Label(
            root,
            textvariable=self.message_var,
            font=tkfont.Font(size=12),
            bg=BACKGROUND_COLOR,
            fg="#f9f6f2",
        )
        self.message_label.pack(fill=tk.X, pady=(0, 8))

        self.canvas = tk.Canvas(
            root,
            width=width,
            height=width,
            bg=BACKGROUND_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack(pady=(0, 20))

        self.font_map = {
            "large": tkfont.Font(size=32, weight="bold"),
            "medium": tkfont.Font(size=28, weight="bold"),
            "small": tkfont.Font(size=22, weight="bold"),
        }

        self._draw_board_background()

        self.board: List[List[Optional[TileWidget]]] = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.tiles: Dict[int, TileWidget] = {}
        self.tile_id_counter = 0
        self.score = 0
        self.best_score = 0

        self.animating = False
        self.animation_state: Optional[Dict[str, object]] = None
        self.start_positions: Dict[int, Tuple[int, int]] = {}

        self.reset_game()
        self.root.bind("<Key>", self.on_key)

    def _build_score_box(self, label: str, value_var: tk.StringVar) -> tk.Frame:
        frame = tk.Frame(self.header, bg="#bbada0", padx=18, pady=10)
        tk.Label(frame, text=label, font=tkfont.Font(size=12, weight="bold"), bg="#bbada0", fg="#eee4da").pack()
        tk.Label(frame, textvariable=value_var, font=tkfont.Font(size=18, weight="bold"), bg="#bbada0", fg="#ffffff").pack()
        return frame

    def _draw_board_background(self) -> None:
        self.canvas.delete("grid")
        board_size_px = GRID_PADDING * 2 + BOARD_SIZE * TILE_SIZE + (BOARD_SIZE - 1) * TILE_GAP
        self.canvas.create_rectangle(
            GRID_PADDING / 2,
            GRID_PADDING / 2,
            board_size_px - GRID_PADDING / 2,
            board_size_px - GRID_PADDING / 2,
            fill=BOARD_BACKGROUND,
            outline="",
            tags="grid",
        )

        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x = GRID_PADDING + col * (TILE_SIZE + TILE_GAP)
                y = GRID_PADDING + row * (TILE_SIZE + TILE_GAP)
                self.canvas.create_rectangle(
                    x,
                    y,
                    x + TILE_SIZE,
                    y + TILE_SIZE,
                    fill=TILE_COLORS[0][0],
                    outline="",
                    tags="grid",
                )

    def reset_game(self) -> None:
        self.animating = False
        self.animation_state = None
        self.start_positions = {}
        self.clear_tiles()
        self.board = [[None] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.tiles = {}
        self.tile_id_counter = 0
        self.score = 0
        self.update_score_boxes()
        self.message_var.set("Use arrow keys or WASD to play")

        self.add_random_tile(animate=False)
        self.add_random_tile(animate=False)

    def clear_tiles(self) -> None:
        for tile in list(self.tiles.values()):
            tile.destroy()
        self.tiles.clear()

    def on_key(self, event: tk.Event) -> None:
        if self.animating:
            return

        key_map = {
            "Left": "left",
            "Right": "right",
            "Up": "up",
            "Down": "down",
            "a": "left",
            "d": "right",
            "w": "up",
            "s": "down",
        }
        direction = key_map.get(event.keysym)
        if not direction:
            return

        self.queue_move(direction)

    def queue_move(self, direction: str) -> None:
        self.start_positions = {tile_id: (tile.row, tile.col) for tile_id, tile in self.tiles.items()}
        moved, movements, merges, _ = self.compute_move(direction)
        if not moved:
            return

        self.animating = True
        self.start_animation(movements, merges)

    def compute_move(
        self, direction: str
    ) -> Tuple[bool, Dict[int, Tuple[int, int]], List[Tuple[int, int]], int]:
        movements: Dict[int, Tuple[int, int]] = {}
        merges: List[Tuple[int, int]] = []
        score_gain = 0

        def line_iterator() -> List[List[Tuple[int, int]]]:
            lines: List[List[Tuple[int, int]]] = []
            if direction == "left":
                for r in range(BOARD_SIZE):
                    lines.append([(r, c) for c in range(BOARD_SIZE)])
            elif direction == "right":
                for r in range(BOARD_SIZE):
                    lines.append([(r, c) for c in reversed(range(BOARD_SIZE))])
            elif direction == "up":
                for c in range(BOARD_SIZE):
                    lines.append([(r, c) for r in range(BOARD_SIZE)])
            elif direction == "down":
                for c in range(BOARD_SIZE):
                    lines.append([(r, c) for r in reversed(range(BOARD_SIZE))])
            return lines

        moved = False
        lines = line_iterator()
        for coords in lines:
            tiles_line = [self.board[r][c] for r, c in coords if self.board[r][c] is not None]
            if not tiles_line:
                continue
            new_line: List[Optional[TileWidget]] = [None] * BOARD_SIZE
            target_index = 0
            idx = 0
            while idx < len(tiles_line):
                current_tile = tiles_line[idx]
                assert current_tile is not None
                current_target = coords[target_index]
                if idx + 1 < len(tiles_line) and tiles_line[idx + 1].value == current_tile.value:
                    next_tile = tiles_line[idx + 1]
                    assert next_tile is not None
                    merges.append((current_tile.tile_id, next_tile.tile_id))
                    current_tile.value *= 2
                    score_gain += current_tile.value
                    movements[current_tile.tile_id] = current_target
                    movements[next_tile.tile_id] = current_target
                    new_line[target_index] = current_tile
                    idx += 2
                else:
                    movements[current_tile.tile_id] = current_target
                    new_line[target_index] = current_tile
                    idx += 1
                target_index += 1

            for fill_index in range(target_index, BOARD_SIZE):
                new_line[fill_index] = None

            for placement_idx, (r, c) in enumerate(coords):
                tile = new_line[placement_idx]
                self.board[r][c] = tile

        for tile_id, (target_row, target_col) in movements.items():
            tile = self.tiles.get(tile_id)
            if tile is None:
                continue
            start = self.start_positions.get(tile_id, (tile.row, tile.col))
            if start != (target_row, target_col):
                moved = True
            tile.row = target_row
            tile.col = target_col

        if merges:
            moved = True

        if moved:
            self.score += score_gain
            if self.score > self.best_score:
                self.best_score = self.score
            self.update_score_boxes()
            if any(tile.value >= WIN_TILE for tile in self.tiles.values()):
                self.message_var.set("You made a 2048 tile! Keep going!")

        return moved, movements, merges, score_gain

    def start_animation(
        self, movements: Dict[int, Tuple[int, int]], merges: List[Tuple[int, int]]
    ) -> None:
        vectors: Dict[int, Tuple[float, float]] = {}
        for tile_id, (target_row, target_col) in movements.items():
            tile = self.tiles.get(tile_id)
            if tile is None:
                continue
            start_row, start_col = self.start_positions.get(tile_id, (target_row, target_col))
            start_x, start_y = tile.grid_to_pixel(start_row, start_col)
            end_x, end_y = tile.grid_to_pixel(target_row, target_col)
            dx = (end_x - start_x) / ANIMATION_STEPS
            dy = (end_y - start_y) / ANIMATION_STEPS
            vectors[tile_id] = (dx, dy)

        self.animation_state = {
            "step": 0,
            "movements": movements,
            "merges": merges,
            "vectors": vectors,
        }
        self.perform_animation_step()

    def perform_animation_step(self) -> None:
        assert self.animation_state is not None
        step = self.animation_state["step"]
        vectors: Dict[int, Tuple[float, float]] = self.animation_state["vectors"]  # type: ignore[assignment]

        if step < ANIMATION_STEPS:
            for tile_id, (dx, dy) in vectors.items():
                tile = self.tiles.get(tile_id)
                if tile is None:
                    continue
                tile.move_by(dx, dy)
            self.animation_state["step"] = step + 1
            self.root.after(ANIMATION_DELAY_MS, self.perform_animation_step)
            return

        movements: Dict[int, Tuple[int, int]] = self.animation_state["movements"]  # type: ignore[assignment]
        merges: List[Tuple[int, int]] = self.animation_state["merges"]  # type: ignore[assignment]

        for tile_id, (target_row, target_col) in movements.items():
            tile = self.tiles.get(tile_id)
            if tile is None:
                continue
            tile.update_position(target_row, target_col)

        for keep_id, remove_id in merges:
            keeper = self.tiles.get(keep_id)
            if keeper is not None:
                keeper.update_style()
            to_remove = self.tiles.get(remove_id)
            if to_remove is not None:
                to_remove.destroy()
                del self.tiles[remove_id]

        self.animation_state = None
        self.animating = False
        self.update_score_boxes()

        self.add_random_tile(animate=True)
        if not self.moves_available():
            self.message_var.set("No more moves! Press R to restart.")
        elif any(tile.value >= WIN_TILE for tile in self.tiles.values()):
            self.message_var.set("You made a 2048 tile! Keep going!")
        else:
            self.message_var.set("Use arrow keys or WASD to play")

    def add_random_tile(self, animate: bool) -> None:
        empties = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if self.board[r][c] is None]
        if not empties:
            return
        row, col = random.choice(empties)
        value = 4 if random.random() < 0.1 else 2
        self.tile_id_counter += 1
        tile = TileWidget(self.tile_id_counter, value, row, col, self.canvas, self.font_map)
        self.tiles[tile.tile_id] = tile
        self.board[row][col] = tile
        tile.update_style()
        if animate:
            self.animate_new_tile(tile, step=0)

    def animate_new_tile(self, tile: TileWidget, step: int) -> None:
        if tile.tile_id not in self.tiles:
            return
        scale = 0.6 + 0.4 * (step / max(1, NEW_TILE_ANIMATION_STEPS))
        x, y = tile.grid_to_pixel(tile.row, tile.col)
        size = TILE_SIZE * scale
        x_offset = (TILE_SIZE - size) / 2
        y_offset = (TILE_SIZE - size) / 2
        self.canvas.coords(tile.rect, x + x_offset, y + y_offset, x + x_offset + size, y + y_offset + size)
        self.canvas.coords(tile.text, x + TILE_SIZE / 2, y + TILE_SIZE / 2)
        if step < NEW_TILE_ANIMATION_STEPS:
            self.root.after(NEW_TILE_DELAY_MS, self.animate_new_tile, tile, step + 1)
        else:
            tile.update_position(tile.row, tile.col)

    def moves_available(self) -> bool:
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                tile = self.board[row][col]
                if tile is None:
                    return True
                for dr, dc in ((0, 1), (1, 0)):
                    nr, nc = row + dr, col + dc
                    if nr < BOARD_SIZE and nc < BOARD_SIZE:
                        neighbor = self.board[nr][nc]
                        if neighbor is None or neighbor.value == tile.value:
                            return True
        return False

    def update_score_boxes(self) -> None:
        self.score_var.set(str(self.score))
        self.best_score = max(self.best_score, self.score)
        self.best_var.set(str(self.best_score))

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    root = tk.Tk()
    app = Game2048App(root)
    root.bind("r", lambda _: app.reset_game())
    root.bind("R", lambda _: app.reset_game())
    app.run()