"""把名稱轉成唯一、檔名與網址安全的 slug（保留 CJK）。"""
from __future__ import annotations

import re
import unicodedata

_UNSAFE = re.compile(r'[\\/:*?"<>|]')
_SPACES = re.compile(r"\s+")
_DASHES = re.compile(r"-+")


def _base_slug(name: str) -> str:
    s = unicodedata.normalize("NFKC", str(name)).strip().lower()
    s = _UNSAFE.sub("", s)
    s = _SPACES.sub("-", s)
    s = _DASHES.sub("-", s).strip("-")
    return s or "game"


def slugify(name: str, taken=None) -> str:
    """回傳唯一 slug；若提供 taken 集合，會避開其中已用過的並把結果加入。"""
    base = _base_slug(name)
    slug = base
    i = 2
    if taken is not None:
        while slug in taken:
            slug = f"{base}-{i}"
            i += 1
        taken.add(slug)
    return slug
