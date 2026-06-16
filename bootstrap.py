# bootstrap.py
"""從已部署的選單 index.html 產生草稿 library.json（純函式，不碰 git/網路）。"""
from __future__ import annotations

import html as _html
import re

import project

_TITLE_RE = re.compile(r"<title>(?P<title>.*?)</title>", re.S)
_CARD_RE = re.compile(
    r'<a class="card"[^>]*>.*?<span>(?P<label>.*?)</span>\s*</a>', re.S)


def draft_project_from_menu(html: str) -> dict:
    """解析部署選單 → 草稿專案 dict（folder 留空、cover/rtp 為 None）。"""
    proj = project.default_project()
    m = _TITLE_RE.search(html)
    if m:
        proj["lib_name"] = _html.unescape(m.group("title").strip())
    games = []
    for cm in _CARD_RE.finditer(html):
        label = _html.unescape(cm.group("label").strip())
        games.append({"folder": "", "label": label, "cover": None, "rtp": None})
    proj["games"] = games
    return proj
