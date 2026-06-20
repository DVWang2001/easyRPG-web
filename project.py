# project.py
"""遊戲庫專案檔（library.json）的載入/儲存與安全閥 —— 純函式，與 GUI 隔離。"""
from __future__ import annotations

import json
import os
from pathlib import Path

import slugify

HERE = Path(__file__).resolve().parent
DEFAULT_ICON = HERE / "assets" / "app_icon.png"
DEFAULT_SOUNDFONT = HERE / "assets" / "easyrpg.soundfont"

VERSION = 1


def default_project() -> dict:
    """完整 schema 的空專案。"""
    return {
        "version": VERSION,
        "lib_name": "我的遊戲庫",
        "icon": str(DEFAULT_ICON),
        "soundfont": str(DEFAULT_SOUNDFONT),
        "out": "dist",
        "all_tags": [],
        "name_tables": [],
        "games": [],
    }


def _normalize(data) -> dict:
    """以 default 為底補齊缺欄位；遷移舊 name_table/custom_player → name_tables/name_table_id。"""
    proj = default_project()
    if isinstance(data, dict):
        for k in ("version", "lib_name", "icon", "soundfont", "out"):
            if data.get(k) is not None:
                proj[k] = data[k]

        # --- name_tables：新格式優先；否則從舊 name_table 遷移 ---
        tables, taken_ids = [], set()
        raw_tables = data.get("name_tables")
        if isinstance(raw_tables, list):
            for t in raw_tables:
                if not isinstance(t, dict):
                    continue
                name = str(t.get("name") or "").strip() or "自訂字表"
                tid = str(t.get("id") or "").strip()
                if not tid or tid in taken_ids:
                    tid = slugify.hash_slug(name, taken_ids)
                taken_ids.add(tid)
                tables.append({"id": tid, "name": name,
                               "zh_tw_1": str(t.get("zh_tw_1") or ""),
                               "zh_tw_2": str(t.get("zh_tw_2") or "")})
        migrated_id = ""
        if not tables:
            old = data.get("name_table")
            z1 = str(old.get("zh_tw_1") or "") if isinstance(old, dict) else ""
            z2 = str(old.get("zh_tw_2") or "") if isinstance(old, dict) else ""
            games_have_custom = any(
                isinstance(g, dict) and g.get("custom_player")
                for g in (data.get("games") or []))
            if z1 or z2 or games_have_custom:
                migrated_id = slugify.hash_slug("自訂字表", taken_ids)
                taken_ids.add(migrated_id)
                tables.append({"id": migrated_id, "name": "自訂字表",
                               "zh_tw_1": z1, "zh_tw_2": z2})
        proj["name_tables"] = tables
        valid_ids = {t["id"] for t in tables}

        # --- games ---
        games = data.get("games")
        if isinstance(games, list):
            norm = []
            for g in games:
                if not isinstance(g, dict):
                    continue
                nid = str(g.get("name_table_id") or "").strip()
                if nid not in valid_ids:
                    nid = migrated_id if g.get("custom_player") else ""
                norm.append({
                    "folder": g.get("folder") or "",
                    "label": g.get("label") or "",
                    "cover": g.get("cover") or None,
                    "rtp": g.get("rtp") or None,
                    "tags": [str(t).strip() for t in (g.get("tags") or [])
                             if str(t).strip()],
                    "name_table_id": nid,
                })
            proj["games"] = norm

        # 全域標籤清單：明確清單（去重去空白）優先，再補上各遊戲用到但不在清單的
        ordered, seen = [], set()
        for t in (data.get("all_tags") or []):
            t = str(t).strip()
            if t and t not in seen:
                seen.add(t)
                ordered.append(t)
        for g in proj["games"]:
            for t in g["tags"]:
                if t not in seen:
                    seen.add(t)
                    ordered.append(t)
        proj["all_tags"] = ordered
    return proj


def load_project(path):
    """讀 library.json。缺檔→(default, None)；壞檔→(default, 警告字串)。永不丟例外。"""
    path = Path(path)
    if not path.exists():
        return default_project(), None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        return default_project(), f"讀取 {path.name} 失敗：{e}（已以空庫開啟）"
    return _normalize(raw), None


def save_project(path, data) -> None:
    """原子寫入 library.json（UTF-8、不跳脫中文、縮排 2）。"""
    path = Path(path)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def missing_sources(games) -> list:
    """回傳『原始資料夾未指定或無效（缺 RPG_RT.ldb/.lmt）』的遊戲顯示名稱清單。"""
    bad = []
    for g in games:
        folder = (g.get("folder") or "").strip()
        ok = bool(folder) and any(
            (Path(folder) / n).exists() for n in ("RPG_RT.ldb", "RPG_RT.lmt"))
        if not ok:
            bad.append(g.get("label") or folder or "（未命名）")
    return bad
