"""把名稱轉成唯一、ASCII-only 的 slug（用作 games/<slug>/ 資料夾名與 ?game= 參數）。

必須是純 ASCII：EasyRPG web player 的 ?game= 不做 URL 解碼、又對值跑 toLowerCase，
非 ASCII（中文等）名稱會壞掉、找不到遊戲目錄。顯示名稱（label）另外保留原文，不受此影響。
"""
from __future__ import annotations

import re
import unicodedata

# 非 ASCII 英數的字元（含中文、空白、& / : * 等）一律轉成分隔線
_NON_ASCII_ALNUM = re.compile(r"[^a-z0-9]+")


def _base_slug(name: str) -> str:
    s = unicodedata.normalize("NFKC", str(name)).lower()
    s = _NON_ASCII_ALNUM.sub("-", s).strip("-")
    return s or "game"


def slugify(name: str, taken=None) -> str:
    """回傳唯一、純 ASCII 的 slug；若提供 taken 集合，會避開已用過的並把結果加入。"""
    base = _base_slug(name)
    slug = base
    i = 2
    if taken is not None:
        while slug in taken:
            slug = f"{base}-{i}"
            i += 1
        taken.add(slug)
    return slug
