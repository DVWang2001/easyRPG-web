"""從 RPG Maker 遊戲的 RPG_RT.exe 抽出取名畫面的中文鍵盤字表（純函式為主）。

字表以「固定間距的記錄陣列」存在 exe 裡：每格前 2 bytes 是一個（Big5 等編碼的）字，
後面接其他資料。以掃描『每格都是合法鍵盤字』的最長連續區段來自動定位，無須寫死位移。
"""
from __future__ import annotations

from pathlib import Path

import nametable

# 鍵盤上的非漢字格（全形英數列、控制鍵、符號）；定位時算有效格，但抽字表時濾掉。
# 有些遊戲鍵盤前幾列是全形英文字母（Ａ-Ｚ ａ-ｚ）與數字，不能讓它們中斷字表偵測。
_SYMBOLS = set("★◆●")
_STRIDES = (12, 16, 8, 10)
_MINRUN = 60
# 真字表幾乎不重複字；重複率高的長串是填充/程式碼雜訊（如同一字連續數百次）→ 剔除。
_UNIQ_RATIO = 0.5

# RPG_RT.ini 的 Encoding 代碼 → Python codec
_ENC_MAP = {"950": "cp950", "936": "gbk", "932": "cp932", "65001": "utf-8"}


def read_encoding(game_folder) -> str:
    """讀 RPG_RT.ini 的 [EasyRPG] Encoding=；缺/未知則預設 cp950（Big5）。"""
    ini = Path(game_folder) / "RPG_RT.ini"
    if ini.exists():
        try:
            for line in ini.read_text(encoding="latin-1").splitlines():
                s = line.strip()
                if s.lower().startswith("encoding"):
                    _, _, val = s.partition("=")
                    return _ENC_MAP.get(val.strip(), "cp950")
        except OSError:
            pass
    return "cp950"


def _is_han(ch: str) -> bool:
    o = ord(ch)
    return 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF


def is_keyboard_cell(b2: bytes, encoding: str):
    """前 2 bytes 是否為合法鍵盤格（漢字或全形數字/符號）；是則回該字，否則 None。"""
    if len(b2) < 2:
        return None
    try:
        ch = b2.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        return None
    if len(ch) != 1:
        return None
    o = ord(ch)
    if _is_han(ch):
        return ch
    if 0xFF01 <= o <= 0xFF5E:        # 全形 ASCII（Ａ-Ｚ ａ-ｚ ０-９ ＜＞ 等）
        return ch
    if o == 0x3000 or ch in _SYMBOLS:  # 全形空白、★◆● 等控制/裝飾格
        return ch
    return None


def _valid_map(data: bytes, encoding: str):
    """每個位移的『該處 2 bytes 是否為鍵盤格字』（是→字，否→None），只算一次重用。"""
    n = len(data)
    vm = [None] * n
    for i in range(n - 1):
        vm[i] = is_keyboard_cell(data[i:i + 2], encoding)
    return vm


def _runs_at_stride(vm, stride: int, minrun: int):
    """在固定步幅下，找出『每步幅都是有效格』的最長連續區段（>=minrun 格）。"""
    runs = []
    n = len(vm)
    i = 0
    while i < n:
        if vm[i] is None:
            i += 1
            continue
        cells = []
        off = i
        while off < n and vm[off] is not None:
            cells.append(vm[off])
            off += stride
        if len(cells) >= minrun:
            runs.append((i, cells))
            i = off  # 跳過此 run，避免重複記子區段
        else:
            i += 1
    return runs


def _diversity(cells) -> int:
    """以『不重複字數』衡量像不像真字表（真字表幾乎全不同字）。"""
    return len(set(cells))


def locate_tables(data: bytes, encoding: str = "cp950",
                  strides=_STRIDES, minrun: int = _MINRUN):
    """回傳最佳步幅下的鍵盤字格連續區段清單 [(offset, [chars]), ...]。

    對候選步幅各掃一遍，先剔除重複率過高的雜訊段，再挑「單段不重複字數最多」的步幅當答案
    （同字表的格都是同一步幅；用多樣性而非長度，避免被大量重複字的填充/程式碼區誤導）。
    """
    vm = _valid_map(data, encoding)
    best, best_q = [], 0
    for s in strides:
        runs = [r for r in _runs_at_stride(vm, s, minrun)
                if _diversity(r[1]) >= _UNIQ_RATIO * len(r[1])]
        q = max((_diversity(c) for _, c in runs), default=0)
        if q > best_q:
            best, best_q = runs, q
    return best


def _game_runs(game_folder, log):
    """讀 RPG_RT.exe → 定位字表段（每段＝遊戲鍵盤的一頁）。找不到回 []。"""
    exe = Path(game_folder) / "RPG_RT.exe"
    if not exe.exists():
        if log:
            log(f"找不到 {exe}")
        return []
    runs = locate_tables(exe.read_bytes(), read_encoding(game_folder))
    if not runs and log:
        log("RPG_RT.exe 內找不到鍵盤字表（可能無內嵌或編碼不符）。")
    return runs


def extract_chars(game_folder, log=None) -> str:
    """回傳遊戲鍵盤所有格的字（忠實保留：漢字＋全形英數＋符號），依頁序串接。找不到回 ""。"""
    runs = sorted(_game_runs(game_folder, log), key=lambda r: r[0])
    return "".join("".join(cells) for _, cells in runs)


def extract_pages(game_folder, log=None):
    """忠實還原遊戲鍵盤 → 回 (zh_tw_1, zh_tw_2)。

    目的是「忠實還原遊戲的字表」：每偵測到的頁＝一頁，原字原序保留（含全形英數字母與
    符號，不只留漢字）。多頁 → 漢一=第一頁、漢二=第二頁；單頁超過一頁容量 → 自動切兩頁。
    各頁上限 nametable.CAPACITY 字。找不到回 ("", "")。
    """
    runs = _game_runs(game_folder, log)
    if not runs:
        return ("", "")
    # 取最像字表的兩段（多樣性最高），再依檔案位移＝頁序排列
    runs = sorted(runs, key=lambda r: _diversity(r[1]), reverse=True)[:2]
    runs = sorted(runs, key=lambda r: r[0])
    cap = nametable.CAPACITY
    pages = ["".join(cells) for _, cells in runs]
    if len(pages) == 1:
        z1, z2 = pages[0][:cap], pages[0][cap:2 * cap]
    else:
        z1, z2 = pages[0][:cap], pages[1][:cap]
    if log:
        log(f"抽到字表：漢一 {len(z1)} 字、漢二 {len(z2)} 字（忠實含英數/符號）。")
    return (z1, z2)
