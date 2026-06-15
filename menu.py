"""產生圖示網格的「遊戲庫選單」index.html。"""
from __future__ import annotations

import html as _html
from pathlib import Path
from urllib.parse import quote

import pwa

_PAGE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>__PWAHEAD__
<style>
* { box-sizing: border-box; }
body { margin:0; background:#111; color:#eee;
  font-family:-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif; }
header { padding:20px 16px; text-align:center; font-size:20px; font-weight:600; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(110px,1fr));
  gap:16px; padding:8px 16px 32px; }
.card { display:flex; flex-direction:column; align-items:center;
  text-decoration:none; color:inherit; }
.card img { width:100%; aspect-ratio:1/1; object-fit:cover; border-radius:16px;
  background:#222; box-shadow:0 2px 8px rgba(0,0,0,.5); }
.card span { margin-top:8px; font-size:14px; text-align:center; word-break:break-word; }
.card:active { transform:scale(.96); }
</style>
</head>
<body>
<header>__TITLE__</header>
<div class="grid">
__CARDS__
</div>
</body>
</html>
"""

_CARD = '<a class="card" href="__HREF__"><img src="__COVER__" alt=""><span>__LABEL__</span></a>'


def write_menu(dist, app_label: str, entries, icon_rel: str = pwa.ICON_REL) -> Path:
    cards = []
    for e in entries:
        href = "play.html?game=" + quote(e["slug"])
        cover = e["cover_rel"] or icon_rel
        card = (
            _CARD.replace("__HREF__", _html.escape(href, quote=True))
            .replace("__COVER__", _html.escape(cover, quote=True))
            .replace("__LABEL__", _html.escape(e["label"]))
        )
        cards.append(card)
    page = (
        _PAGE.replace("__PWAHEAD__", pwa.pwa_head(app_label, icon_rel))
        .replace("__TITLE__", _html.escape(app_label))
        .replace("__CARDS__", "\n".join(cards))
    )
    out = Path(dist) / "index.html"
    out.write_text(page, encoding="utf-8")
    return out
