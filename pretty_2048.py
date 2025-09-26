"""A vibrant, terminal-based version of 2048 implemented with curses.

Run the script and use the arrow keys to slide tiles around.
Combine matching tiles to reach 2048 (or beyond) while enjoying
colorful feedback and smooth board rendering.
"""
from __future__ import annotations

import curses
import itertools
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


BOARD_SIZE = 4
WIN_TILE = 2048

# Mapping from tile value to (foreground, background) color pair names.
# Colors are defined in ``ColorPalette.setup``.
COLOR_MAP: Dict[int, str] = {
    0: "empty",
    2: "c2",
    4: "c4",
    8: "c8",
    16: "c16",
    32: "c32",
    64: "c64",
    128: "c128",
    256: "c256",
    512: "c512",
    1024: "c1024",
    2048: "c2048",
}


def add_random_tile(board: List[List[int]]) -> bool:
    """Insert a random tile (2 or 4) in an empty spot.

    Returns ``True`` if a tile was placed, otherwise ``False`` when the board
    is full.
    """

    empties = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] == 0]
    if not empties:
        return False

    r, c = random.choice(empties)
    board[r][c] = 4 if random.random() < 0.1 else 2
    return True


def compress(line: List[int]) -> Tuple[List[int], bool]:
    """Compress a row or column towards the front, removing zeros."""

    new_line = [value for value in line if value != 0]
    did_compress = len(new_line) != len(line)
    new_line.extend([0] * (len(line) - len(new_line)))
    return new_line, did_compress


def merge(line: List[int]) -> Tuple[List[int], int]:
    """Merge a compressed line and return the new line and score gained."""

    score = 0
    for i in range(len(line) - 1):
        if line[i] != 0 and line[i] == line[i + 1]:
            line[i] *= 2
            line[i + 1] = 0
            score += line[i]
    return line, score


def reverse(line: List[int]) -> List[int]:
    return list(reversed(line))


def transpose(board: List[List[int]]) -> List[List[int]]:
    return [list(row) for row in zip(*board)]


def move_left(board: List[List[int]]) -> Tuple[List[List[int]], int, bool]:
    score_gain = 0
    moved = False
    new_board: List[List[int]] = []

    for row in board:
        compressed, did_compress = compress(row)
        merged, gained = merge(compressed)
        compressed_after_merge, did_compress_again = compress(merged)
        new_board.append(compressed_after_merge)
        score_gain += gained
        moved = moved or did_compress or did_compress_again or gained > 0

    return new_board, score_gain, moved


def move_right(board: List[List[int]]) -> Tuple[List[List[int]], int, bool]:
    reversed_rows = [reverse(row) for row in board]
    moved_board, score_gain, moved = move_left(reversed_rows)
    restored = [reverse(row) for row in moved_board]
    return restored, score_gain, moved


def move_up(board: List[List[int]]) -> Tuple[List[List[int]], int, bool]:
    transposed = transpose(board)
    moved_board, score_gain, moved = move_left(transposed)
    restored = transpose(moved_board)
    return restored, score_gain, moved


def move_down(board: List[List[int]]) -> Tuple[List[List[int]], int, bool]:
    transposed = transpose(board)
    moved_board, score_gain, moved = move_right(transposed)
    restored = transpose(moved_board)
    return restored, score_gain, moved


MOVES = {
    curses.KEY_LEFT: move_left,
    curses.KEY_RIGHT: move_right,
    curses.KEY_UP: move_up,
    curses.KEY_DOWN: move_down,
}


@dataclass
class GameState:
    board: List[List[int]] = field(default_factory=lambda: [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)])
    score: int = 0
    best_score: int = 0
    won: bool = False
    over: bool = False

    def reset(self) -> None:
        self.board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.score = 0
        self.won = False
        self.over = False
        add_random_tile(self.board)
        add_random_tile(self.board)

    def apply_move(self, move_func) -> None:
        if self.over:
            return

        new_board, gained, moved = move_func(self.board)
        if not moved:
            return

        self.board = new_board
        self.score += gained
        if self.score > self.best_score:
            self.best_score = self.score
        add_random_tile(self.board)
        self.won = self.won or any(tile >= WIN_TILE for tile in itertools.chain.from_iterable(self.board))
        if not any(valid_move_available(self.board, func) for func in MOVES.values()):
            self.over = True


@dataclass
class ColorPalette:
    pairs: Dict[str, int] = field(default_factory=dict)

    def setup(self) -> None:
        curses.start_color()
        curses.use_default_colors()

        def add_pair(name: str, fg: int, bg: int) -> None:
            index = len(self.pairs) + 1
            curses.init_pair(index, fg, bg)
            self.pairs[name] = index

        add_pair("empty", curses.COLOR_WHITE, -1)
        add_pair("c2", curses.COLOR_YELLOW, -1)
        add_pair("c4", curses.COLOR_MAGENTA, -1)
        add_pair("c8", curses.COLOR_CYAN, -1)
        add_pair("c16", curses.COLOR_GREEN, -1)
        add_pair("c32", curses.COLOR_BLUE, -1)
        add_pair("c64", curses.COLOR_RED, -1)
        add_pair("c128", curses.COLOR_YELLOW, curses.COLOR_BLACK)
        add_pair("c256", curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        add_pair("c512", curses.COLOR_CYAN, curses.COLOR_BLACK)
        add_pair("c1024", curses.COLOR_GREEN, curses.COLOR_BLACK)
        add_pair("c2048", curses.COLOR_RED, curses.COLOR_BLACK)

    def color_for(self, value: int) -> int:
        name = COLOR_MAP.get(value, "c2048")
        pair_index = self.pairs.get(name, 0)
        return curses.color_pair(pair_index)


def valid_move_available(board: List[List[int]], move_func) -> bool:
    new_board, _, moved = move_func(board)
    return moved


def draw_board(stdscr, state: GameState, palette: ColorPalette) -> None:
    stdscr.clear()

    height, width = stdscr.getmaxyx()
    board_width = BOARD_SIZE * 6 + 1
    board_height = BOARD_SIZE * 2 + 1
    offset_y = max(2, (height - board_height) // 2)
    offset_x = max(2, (width - board_width) // 2)

    title = "✨ Fancy 2048 ✨"
    stdscr.attron(curses.A_BOLD)
    stdscr.addstr(1, max(2, (width - len(title)) // 2), title)
    stdscr.attroff(curses.A_BOLD)

    info = f"Score: {state.score}  |  Best: {state.best_score}"
    stdscr.addstr(offset_y - 2, max(2, (width - len(info)) // 2), info)

    if state.won:
        stdscr.addstr(offset_y + board_height + 1, offset_x, "You made it to 2048! Keep going if you like.", curses.A_BOLD)
    if state.over:
        stdscr.addstr(offset_y + board_height + 2, offset_x, "No more moves! Press 'r' to restart or 'q' to quit.", curses.A_BOLD)
    else:
        stdscr.addstr(offset_y + board_height + 2, offset_x, "Use arrow keys to slide tiles. Press 'q' to quit, 'r' to restart.")

    # Draw horizontal borders
    horizontal_border = "+" + "+".join("-" * 5 for _ in range(BOARD_SIZE)) + "+"
    for r in range(BOARD_SIZE + 1):
        y = offset_y + r * 2
        stdscr.addstr(y, offset_x, horizontal_border)

    # Draw cells with vertical separators and colorized text
    for r in range(BOARD_SIZE):
        row_y = offset_y + r * 2 + 1
        stdscr.addch(row_y, offset_x, "|")
        for c in range(BOARD_SIZE):
            value = state.board[r][c]
            text = f"{value}" if value else ""
            cell_width = 5
            padded = text.center(cell_width)
            attr = palette.color_for(value)
            if attr:
                stdscr.attron(attr | curses.A_BOLD)
            stdscr.addstr(row_y, offset_x + 1 + c * 6, padded)
            if attr:
                stdscr.attroff(attr | curses.A_BOLD)
            stdscr.addch(row_y, offset_x + (c + 1) * 6, "|")

    stdscr.refresh()


def game_loop(stdscr) -> None:
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)

    palette = ColorPalette()
    palette.setup()

    state = GameState()
    state.reset()

    draw_board(stdscr, state, palette)

    while True:
        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            break
        if key in (ord("r"), ord("R")):
            state.reset()
            draw_board(stdscr, state, palette)
            continue
        move_func = MOVES.get(key)
        if move_func is None:
            continue
        state.apply_move(move_func)
        draw_board(stdscr, state, palette)


def main() -> None:
    try:
        curses.wrapper(game_loop)
    except curses.error:
        print("This game needs a terminal that supports color and cursor movement.")
        print("Try resizing your terminal or running it locally in a full-featured terminal emulator.")


if __name__ == "__main__":
    main()
