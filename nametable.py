"""把使用者輸入的中文字產生成 EasyRPG Player 的繁中取名字表（純函式）。

以 EasyRPG `window_keyboard.cpp` 為樣板，替換 Trad. Chinese 1/2 兩頁的 9×10 字格，
依序填入使用者的字（保留 SPACE/NEXT_PAGE/DONE 控制格），頁籤改成 漢一/漢二。
"""
from __future__ import annotations

import re

ROWS, COLS = 9, 10
CAPACITY = 8 * COLS + 6  # 每頁可填字數（前 8 列全填 + 第 9 列前 6 格）＝86
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


def _esc_label(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def render(template: str, pages) -> str:
    """回傳替換過繁中兩頁字表與頁籤名的 window_keyboard.cpp 文字。

    pages：頁清單 [{label, chars}, …]。EasyRPG 鍵盤只有兩頁(ZhTw1/ZhTw2)，故只用
    前兩頁：不足補空頁，超過則截斷（取前兩頁）。各頁 label 成為頁籤名（包成 <label>）。
    也相容舊呼叫 render(template, zh_tw_1_str, zh_tw_2_str)。
    """
    if isinstance(pages, str):  # 舊式 (template, zh_tw_1, zh_tw_2) 不再支援單獨字串
        raise TypeError("render(template, pages) 需傳頁清單，不是字串")

    def page(i, default_label):
        if i < len(pages):
            p = pages[i]
            return (str(p.get("label") or default_label), str(p.get("chars") or ""))
        return (default_label, "")

    l1, c1 = page(0, "漢一")
    l2, c2 = page(1, "漢二")
    out = re.sub(r"\{ // Trad\. Chinese 1\n.*?\n\t\t\}",
                 lambda m: _inner("Trad. Chinese 1", c1), template,
                 count=1, flags=re.S)
    out = re.sub(r"\{ // Trad\. Chinese 2\n.*?\n\t\t\}",
                 lambda m: _inner("Trad. Chinese 2", c2), out,
                 count=1, flags=re.S)
    out = out.replace('"<翻頁>"', '"<' + _esc_label(l1) + '>"', 1)
    out = out.replace('"<前頁>"', '"<' + _esc_label(l2) + '>"', 1)
    return out
