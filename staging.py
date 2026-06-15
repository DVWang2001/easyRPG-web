"""把遊戲資料夾 staging 進輸出夾：套排除規則、注入 SF2、選灌 RTP。"""
from __future__ import annotations

import fnmatch
import shutil
from pathlib import Path

DEFAULT_IGNORE = ("*.bak", "*.trans", "index.json", "Thumbs.db", ".DS_Store", "gencache*")
SOUNDFONT_NAME = "easyrpg.soundfont"


def _ignored(rel_posix: str, name: str, ignore_globs, exclude_set) -> bool:
    if rel_posix in exclude_set:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in ignore_globs)


def _ancestors(rel: Path):
    parts = rel.parts
    for i in range(1, len(parts)):
        yield Path(*parts[:i]).as_posix()


def _copy_tree(src: Path, dest: Path, ignore_globs, exclude_set):
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        rel_posix = rel.as_posix()
        if _ignored(rel_posix, item.name, ignore_globs, exclude_set):
            continue
        if any(anc in exclude_set for anc in _ancestors(rel)):
            continue
        target = dest / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def stage_game(game_dir, dest, *, ignore_globs=DEFAULT_IGNORE,
               exclude_paths=(), soundfont=None, rtp=None) -> None:
    game_dir = Path(game_dir)
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    exclude_set = {Path(p).as_posix() for p in exclude_paths}

    if rtp:
        _copy_tree(Path(rtp), dest, ignore_globs, exclude_set)
    _copy_tree(game_dir, dest, ignore_globs, exclude_set)

    if soundfont:
        shutil.copy2(Path(soundfont), dest / SOUNDFONT_NAME)
