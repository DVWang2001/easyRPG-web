"""把多個遊戲各自 staging 到 dist/games/<slug>/，產 index.json，複製封面。"""
from __future__ import annotations

import shutil
from pathlib import Path

import gencache
import staging


def stage_library(out, games, *, soundfont=None, ignore_globs=staging.DEFAULT_IGNORE):
    """games: list of {folder, label, slug, cover(optional)}。
    回傳選單用 entries: list of {label, slug, cover_rel}。"""
    out = Path(out)
    entries = []
    for g in games:
        slug = g["slug"]
        dest = out / "games" / slug
        staging.stage_game(g["folder"], dest, ignore_globs=ignore_globs, soundfont=soundfont)
        gencache.write_index(dest)  # 在複製封面前產索引，封面就不會進 index.json
        cover_rel = None
        if g.get("cover"):
            shutil.copy2(Path(g["cover"]), dest / "cover.png")
            cover_rel = f"games/{slug}/cover.png"
        entries.append({"label": g["label"], "slug": slug, "cover_rel": cover_rel})
    return entries
