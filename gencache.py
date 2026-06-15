"""純 Python 重寫 EasyRPG 的 gencache 工具。

EasyRPG web player 需要 index.json，因為 RPG Maker 遊戲引用檔案時不帶副檔名。
本實作忠於 EasyRPG/Tools gencache (src/main.cpp)：NFKC-normalised 小寫 key、
除根層與 .ini/.po 外去副檔名、每個子目錄帶 _dirname、exfont 特例、metadata version 2。
"""
from __future__ import annotations

import json
import os
import unicodedata
from datetime import date
from pathlib import Path

KEEP_EXTENSION = (".ini", ".po")
DEFAULT_DEPTH = 4


def _norm(name: str) -> str:
    # C++ 是 ICU toLower(root locale) 後 NFKC normalize。
    return unicodedata.normalize("NFKC", name.lower())


def _strip_ext(name: str) -> str:
    dot = name.rfind(".")
    return name if dot < 0 else name[:dot]


def _keep_extension(lower_name: str) -> bool:
    return lower_name.endswith(KEEP_EXTENSION)


def _walk(path: Path, depth: int, first: bool = False) -> dict:
    if depth == 0:
        return {}
    try:
        entries = list(os.scandir(path))
    except OSError:
        return {}
    result: dict = {}
    if not first:
        result["_dirname"] = path.name
    for entry in entries:
        original = entry.name
        if original == "_dirname":
            continue
        lower = _norm(original)
        if entry.is_dir():
            sub = _walk(Path(entry.path), depth - 1)
            if sub:
                result[lower] = sub
        elif entry.is_file():
            if first or _keep_extension(lower):
                key = "exfont" if _strip_ext(lower) == "exfont" else lower
                result[key] = original
            else:
                result[_strip_ext(lower)] = original
    return result


def generate_index(game_dir, depth: int = DEFAULT_DEPTH) -> dict:
    cache = _walk(Path(game_dir), depth, first=True)
    return {
        "metadata": {"version": 2, "date": date.today().isoformat()},
        "cache": cache,
    }


def write_index(game_dir, output=None, depth: int = DEFAULT_DEPTH) -> Path:
    game_dir = Path(game_dir)
    output = Path(output) if output else game_dir / "index.json"
    data = generate_index(game_dir, depth)
    output.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    return output


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print("written:", write_index(target))
