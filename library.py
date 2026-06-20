"""把多個遊戲各自 staging 到 dist/games/<slug>/，產 index.json，複製封面。"""
from __future__ import annotations

import shutil
from pathlib import Path

import gencache
import staging


def stage_library(out, games, *, soundfont=None, ignore_globs=staging.DEFAULT_IGNORE):
    """games: list of {folder, label, slug, cover(opt), tags(opt), name_table_id(opt)}。
    回傳選單用 entries: list of {label, slug, cover_rel, tags, name_table_id}。"""
    out = Path(out)
    entries = []
    for g in games:
        slug = g["slug"]
        dest = out / "games" / slug
        staging.stage_game(g["folder"], dest, ignore_globs=ignore_globs,
                           soundfont=soundfont, rtp=g.get("rtp"))
        gencache.write_index(dest)  # 在複製封面前產索引，封面就不會進 index.json
        cover_rel = None
        if g.get("cover"):
            ext = Path(g["cover"]).suffix or ".png"
            shutil.copy2(Path(g["cover"]), dest / f"cover{ext}")
            cover_rel = f"games/{slug}/cover{ext}"
        entries.append({"label": g["label"], "slug": slug, "cover_rel": cover_rel,
                        "tags": list(g.get("tags") or []),
                        "name_table_id": str(g.get("name_table_id") or "")})
    return entries
