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

# 已知的內建字表特徵（抽出的字含全部 marker 子字串即視為該字表）。
# 聖靈火神 RPG Maker 2003 中文化：一頁全形英文＋這串漢字，另一頁中文人名用字。
_KNOWN_TABLES = (
    ("聖靈火神2003字表",
     ("子力小大天中太夫月幻日毛文古艾白玉世冬加",
      "貝利芙芬拉欣東雨依武秀金耶肯青法奇皇宜兒昂")),
)

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
            runs.append((i, cells, stride))
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
        q = max((_diversity(r[1]) for r in runs), default=0)
        if q > best_q:
            best, best_q = runs, q
    return best


def _label_after(data: bytes, end_off: int, encoding: str) -> str:
    """字表段結束後找 <…> 控制格，回傳 <> 內的字當頁名；找不到回 ""。

    頁籤以 ASCII '<'(0x3C) … '>'(0x3E) 包住一段 Big5 字（如 <漢一>、<頁２>）。
    """
    window = data[end_off:end_off + 64]
    lt = window.find(b"\x3c")
    gt = window.find(b"\x3e", lt + 1) if lt >= 0 else -1
    if lt < 0 or gt < 0:
        return ""
    try:
        s = window[lt + 1:gt].decode(encoding)
    except (UnicodeDecodeError, LookupError):
        return ""
    return "".join(ch for ch in s if not ch.isspace())[:8]


def extract_table(game_folder, log=None) -> list:
    """忠實還原遊戲鍵盤 → 回頁清單 [{label, chars}, …]。

    每偵測到的字表段＝一頁，原字原序保留（含全形英數字母與符號，不只留漢字）；
    頁名(label)從 exe 的 <…> 頁籤抽出，抽不到則用「頁N」。各頁上限 nametable.CAPACITY 字。
    依檔案位移＝頁序排列。找不到回 []。
    """
    exe = Path(game_folder) / "RPG_RT.exe"
    if not exe.exists():
        if log:
            log(f"找不到 {exe}")
        return []
    data = exe.read_bytes()
    enc = read_encoding(game_folder)
    runs = locate_tables(data, enc)
    if not runs:
        if log:
            log("RPG_RT.exe 內找不到鍵盤字表（可能無內嵌或編碼不符）。")
        return []
    runs = sorted(runs, key=lambda r: r[0])  # 依位移＝頁序
    cap = nametable.CAPACITY
    pages = []
    for i, (off, cells, stride) in enumerate(runs):
        label = _label_after(data, off + len(cells) * stride, enc) or f"頁{i + 1}"
        pages.append({"label": label, "chars": "".join(cells)[:cap]})
    if log:
        log(f"抽到 {len(pages)} 頁字表：" + "、".join(
            f"{p['label']}({len(p['chars'])}字)" for p in pages))
    return pages


def extract_chars(game_folder, log=None) -> str:
    """回傳遊戲鍵盤所有格的字（依頁序串接），方便除錯/全庫掃描。找不到回 ""。"""
    return "".join(p["chars"] for p in extract_table(game_folder, log))


def recognize(pages) -> str:
    """若抽出的頁清單符合某個已知內建字表，回傳它的名稱（如「聖靈火神2003字表」），否則回 ""。"""
    allchars = "".join(p.get("chars") or "" for p in (pages or []))
    for name, markers in _KNOWN_TABLES:
        if all(m in allchars for m in markers):
            return name
    return ""
