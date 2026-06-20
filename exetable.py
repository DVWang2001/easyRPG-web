"""從 RPG Maker 遊戲的 RPG_RT.exe 抽出取名畫面的中文鍵盤字表（純函式為主）。

字表以「固定間距的記錄陣列」存在 exe 裡：每格前 2 bytes 是一個（Big5 等編碼的）字，
後面接其他資料。以掃描『每格都是合法鍵盤字』的最長連續區段來自動定位，無須寫死位移。
"""
from __future__ import annotations

from pathlib import Path

import nametable

# 鍵盤上的非漢字格（數字列與控制鍵）；定位時算有效格，但抽字表時濾掉。
_FULLWIDTH = set("１２３４５６７８９０＜＞★◆●　")
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
    if _is_han(ch) or ch in _FULLWIDTH:
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


def _collect_chars(runs) -> str:
    """把所有字表段的漢字依『檔案位移順序』去重串起來。

    遊戲的鍵盤可能只有一段（一頁）或多段（多頁）；漢一/漢二是 EasyRPG 鍵盤的兩頁，
    不是遊戲固有結構，故這裡只收集字、不假設頁數。
    """
    seen, out = set(), []
    for _, cells in sorted(runs, key=lambda r: r[0]):
        for c in cells:
            if _is_han(c) and c not in seen:
                seen.add(c)
                out.append(c)
    return "".join(out)


def extract_chars(game_folder, log=None) -> str:
    """讀 RPG_RT.exe → 定位所有字表 → 回傳該遊戲鍵盤的名字用字（去重、依序）。找不到回 ""。"""
    folder = Path(game_folder)
    exe = folder / "RPG_RT.exe"
    if not exe.exists():
        if log:
            log(f"找不到 {exe}")
        return ""
    enc = read_encoding(folder)
    runs = locate_tables(exe.read_bytes(), enc)
    if not runs:
        if log:
            log("RPG_RT.exe 內找不到鍵盤字表（可能無內嵌或編碼不符）。")
        return ""
    return _collect_chars(runs)


def extract_pages(game_folder, log=None):
    """抽出名字用字後，依 EasyRPG 兩頁（各 nametable.CAPACITY 字）切成 (zh_tw_1, zh_tw_2)。

    一律把抽到的字依序填進 漢一(前段)/漢二(次段)，與遊戲原本有幾頁無關。找不到回 ("", "")。
    """
    chars = extract_chars(game_folder, log=log)
    cap = nametable.CAPACITY
    z1, z2 = chars[:cap], chars[cap:2 * cap]
    if log and chars:
        log(f"抽到 {len(chars)} 個名字用字（漢一 {len(z1)}、漢二 {len(z2)}）。")
    return (z1, z2)
