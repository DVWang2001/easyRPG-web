"""把使用者輸入的中文字產生成 EasyRPG Player 的繁中取名字表（純函式）。

以 EasyRPG `window_keyboard.cpp` 為樣板，替換 Trad. Chinese 1/2 兩頁的 9×10 字格，
依序填入使用者的字（保留 SPACE/NEXT_PAGE/DONE 控制格），頁籤改成 漢一/漢二。
"""
from __future__ import annotations

import re

ROWS, COLS = 9, 10
_NEXT = object()  # NEXT_PAGE 控制格（輸出為裸識別字）
_DONE = object()  # DONE 控制格


def _grid(chars: str):
    cells = [c for c in chars if not c.isspace()]
    grid = [["" for _ in range(COLS)] for _ in range(ROWS)]
    # 字格：第 0..7 列全部 10 欄，第 8 列只前 6 欄（其餘留給控制格）。
    slots = [(r, c) for r in range(8) for c in range(COLS)] + [(8, c) for c in range(6)]
    for ch, (r, c) in zip(cells, slots):
        grid[r][c] = ch
    grid[8][6] = _NEXT
    grid[8][8] = _DONE
    return grid


def _cell(cell) -> str:
    if cell is _NEXT:
        return "NEXT_PAGE"
    if cell is _DONE:
        return "DONE"
    return '"' + cell.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _inner(comment: str, chars: str) -> str:
    rows = _grid(chars)
    body = ",\n".join(
        "\t\t\t{" + ", ".join(_cell(c) for c in row) + "}" for row in rows)
    return "{ // " + comment + "\n" + body + "\n\t\t}"


def render(template: str, zh_tw_1: str, zh_tw_2: str) -> str:
    """回傳替換過繁中兩頁字表與頁籤的 window_keyboard.cpp 文字。"""
    out = re.sub(r"\{ // Trad\. Chinese 1\n.*?\n\t\t\}",
                 lambda m: _inner("Trad. Chinese 1", zh_tw_1), template,
                 count=1, flags=re.S)
    out = re.sub(r"\{ // Trad\. Chinese 2\n.*?\n\t\t\}",
                 lambda m: _inner("Trad. Chinese 2", zh_tw_2), out,
                 count=1, flags=re.S)
    out = out.replace('"<翻頁>"', '"<漢一>"', 1)
    out = out.replace('"<前頁>"', '"<漢二>"', 1)
    return out
