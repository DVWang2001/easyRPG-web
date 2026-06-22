"""產生圖示網格的「遊戲庫選單」index.html（含搜尋框與點擊標籤篩選）。"""
from __future__ import annotations

import html as _html
import json
from pathlib import Path

import project
import pwa

_PAGE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>__PWAHEAD__
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Silkscreen&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; }
:root {
  --bg:#0c0e18; --panel:#141828; --ink:#eef1ff; --muted:#8b93bf;
  --line:#262c44; --chip:#171c2e; --chip-line:#2c3350;
  --gold:#f5c542; --win-top:#3f5fcc; --win-bot:#16225e; --win-hi:#9fb4ff; --win-lo:#0a1140;
}
body { margin:0; min-height:100vh; color:var(--ink);
  background:radial-gradient(1100px 560px at 50% -8%, #1a2143 0%, transparent 62%), var(--bg);
  font-family:-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif; }

/* 標題列 */
header { padding:30px 16px 2px; text-align:center; }
.wordmark { margin:0; font-size:26px; font-weight:800; letter-spacing:.04em; }
.eyebrow { margin:9px 0 0; font-family:"Silkscreen",monospace; font-size:11px;
  letter-spacing:.18em; color:var(--gold);
  display:flex; gap:10px; align-items:center; justify-content:center; }
.eyebrow .count { color:var(--ink); }
#me-link { position:fixed; top:12px; right:12px; z-index:5; text-decoration:none;
  padding:6px 12px; border-radius:10px; border:1px solid var(--chip-line);
  background:var(--chip); color:var(--muted); font-size:13px; }
#me-link:hover { border-color:var(--gold); color:var(--ink); }

/* 工具列 */
.toolbar { max-width:980px; margin:0 auto; padding:14px 16px 6px;
  display:flex; flex-direction:column; gap:10px; }
#q { width:100%; padding:11px 14px; border-radius:12px; border:1px solid var(--line);
  background:var(--panel); color:var(--ink); font-size:16px; }
#q::placeholder { color:var(--muted); }
#q:focus { outline:none; border-color:var(--gold); box-shadow:0 0 0 3px rgba(245,197,66,.18); }
.tags { display:flex; flex-direction:column; gap:6px; align-items:flex-start; }
.taggroup { display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
.tagcat { color:var(--muted); font-size:12px; min-width:60px; }
.tagfilter { padding:5px 12px; border-radius:999px; border:1px solid var(--chip-line);
  background:var(--chip); color:#c3c9ea; font-size:13px; cursor:pointer;
  transition:border-color .15s ease, background .15s ease, color .15s ease; }
.tagfilter:hover { border-color:var(--gold); color:#fff; }
.tagfilter.active { background:var(--gold); color:#1a1400; border-color:var(--gold); font-weight:700; }
#clear { padding:5px 12px; border-radius:999px; border:1px solid transparent;
  background:transparent; color:var(--muted); font-size:13px; cursor:pointer; }
#clear:hover { color:var(--ink); }
.toggles { display:flex; gap:8px; }
#empty { display:none; text-align:center; color:var(--muted); padding:24px; }

/* 遊戲格＝選單項 */
.grid { max-width:980px; margin:0 auto;
  display:grid; grid-template-columns:repeat(auto-fill,minmax(116px,1fr));
  gap:20px 14px; padding:12px 16px 44px; }
.card { position:relative; display:flex; flex-direction:column; align-items:center;
  text-decoration:none; color:inherit; -webkit-tap-highlight-color:transparent; }
.card[hidden] { display:none; }
/* 金色 ▶ 選取游標：平時收進去，焦點/hover 滑出（RM 選單點綴） */
.card::before { content:"\25B6"; position:absolute; left:-3px; top:calc(50% - 24px);
  color:var(--gold); font-size:14px; opacity:0; transform:translateX(-7px);
  text-shadow:0 0 8px rgba(245,197,66,.65); pointer-events:none;
  transition:opacity .18s ease, transform .18s ease; }
.thumb { position:relative; width:100%; aspect-ratio:1/1; border-radius:14px;
  overflow:hidden; background:var(--panel); border:1px solid var(--line);
  box-shadow:0 2px 8px rgba(0,0,0,.5);
  transition:transform .2s cubic-bezier(.2,.7,.2,1), box-shadow .2s ease, border-color .2s ease; }
.thumb img { width:100%; height:100%; object-fit:cover; display:block;
  transition:transform .3s cubic-bezier(.2,.7,.2,1); }
.card .name { margin-top:9px; font-size:14px; text-align:center; word-break:break-word;
  color:#cfd5f5; transition:color .18s ease; }
/* hover：金框＋游標滑入（只在真有指標的裝置，手機不卡住） */
@media (hover:hover) and (pointer:fine) {
  .card:hover .thumb { transform:translateY(-3px); border-color:var(--gold);
    box-shadow:0 12px 26px rgba(0,0,0,.55), 0 0 0 1px var(--gold), 0 8px 22px rgba(245,197,66,.22); }
  .card:hover .thumb img { transform:scale(1.05); }
  .card:hover::before { opacity:1; transform:translateX(0); }
  .card:hover .name { color:#fff; }
}
/* 手機按壓回饋 */
.card:active .thumb { transform:scale(.97); transition:transform .1s ease; }
/* 鍵盤聚焦：同樣亮金框＋游標 */
.card:focus-visible { outline:none; }
.card:focus-visible::before { opacity:1; transform:translateX(0); }
.card:focus-visible .thumb { border-color:var(--gold); box-shadow:0 0 0 2px var(--gold); }
@media (prefers-reduced-motion:reduce) {
  .thumb, .thumb img, .card .name, .card::before { transition:none; }
}
/* 卡片標籤晶片 */
.cardtags { text-align:center; line-height:1.7; }
.card .tag { display:inline-block; margin:5px 3px 0; padding:1px 8px; border-radius:999px;
  background:var(--chip); color:#9aa2cc; font-size:11px; cursor:pointer; border:1px solid var(--chip-line); }
.card .tag.active { background:var(--gold); color:#1a1400; border-color:var(--gold); }
body.favonly .card:not(.is-fav) { display:none; }
</style>
<link rel="stylesheet" href="favorites.css">
<link rel="stylesheet" href="popular.css">
<link rel="stylesheet" href="announce.css">
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.8/dist/purify.min.js"></script>
</head>
<body>
<a href="profile.html" id="me-link">👤 我的</a>
<header>
<h1 class="wordmark">__TITLE__</h1>
<p class="eyebrow">▶ SELECT A GAME<span class="count">×__COUNT__</span></p>
</header>
<div id="announce" hidden></div>
<div class="toolbar">
<input id="q" type="search" placeholder="搜尋遊戲或標籤…" autocomplete="off">
<div class="tags" id="tagbar">__TAGFILTERS__<button id="clear">清除篩選</button></div>
<div class="toggles"><button id="favonly">❤ 只看收藏</button><button id="hot">🔥 熱門</button></div>
</div>
<div class="grid" id="grid">
__CARDS__
</div>
<div id="empty">找不到符合的遊戲</div>
<script>
(function(){
  var q = document.getElementById('q');
  var grid = document.getElementById('grid');
  var empty = document.getElementById('empty');
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
  var selected = new Set();

  function cardTags(c){
    var t = c.getAttribute('data-tags');
    return t ? t.split(',') : [];
  }
  function apply(){
    var query = q.value.trim().toLowerCase();
    var shown = 0;
    cards.forEach(function(c){
      var label = c.getAttribute('data-label') || '';
      var tags = cardTags(c);
      var matchesQuery = !query || label.indexOf(query) !== -1 ||
        tags.some(function(t){ return t.indexOf(query) !== -1; });
      var hasAll = true;
      selected.forEach(function(t){ if (tags.indexOf(t) === -1) hasAll = false; });
      var show = matchesQuery && hasAll;
      c.hidden = !show;
      if (show) shown++;
    });
    empty.style.display = shown ? 'none' : 'block';
    document.querySelectorAll('[data-tag]').forEach(function(el){
      if (selected.has(el.getAttribute('data-tag'))) el.classList.add('active');
      else el.classList.remove('active');
    });
  }
  function toggle(tag){
    if (selected.has(tag)) selected.delete(tag); else selected.add(tag);
    apply();
  }
  q.addEventListener('input', apply);
  document.getElementById('clear').addEventListener('click', function(){
    selected.clear(); q.value = ''; apply();
  });
  document.querySelectorAll('.tagfilter').forEach(function(b){
    b.addEventListener('click', function(){ toggle(b.getAttribute('data-tag')); });
  });
  grid.querySelectorAll('.card .tag').forEach(function(s){
    s.addEventListener('click', function(e){
      e.preventDefault(); e.stopPropagation();
      toggle(s.getAttribute('data-tag'));
    });
  });
  apply();
})();
</script>
<script type="module" src="favorites.js"></script>
<script type="module" src="popular.js"></script>
<script type="module" src="announce.js"></script>
</body>
</html>
"""

_CARD = ('<a class="card" href="__HREF__" data-label="__DLABEL__" data-tags="__DTAGS__">'
         '<span class="thumb"><img src="__COVER__" alt=""></span>'
         '<span class="name">__LABEL__</span>'
         '<span class="cardtags">__CARDTAGS__</span></a>')


_PROFILE_PAGE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>我的 · __TITLE__</title>__PWAHEAD__
<link rel="stylesheet" href="profile.css">
</head>
<body>
<div class="pf-top">
<a href="index.html" class="pf-back">← 返回遊戲庫</a>
<strong class="pf-title">我的</strong>
<span id="me-auth" class="pf-auth"></span>
</div>
<section class="pf-section"><h2>我的收藏</h2><div id="my-favs" class="pf-grid"></div></section>
<section class="pf-section"><h2>最近遊玩</h2><div id="my-history" class="pf-grid"></div></section>
__GAMES__
<script type="module" src="profile.js"></script>
</body>
</html>
"""


def write_profile(dist, app_label: str, entries, icon_rel: str = pwa.ICON_REL) -> Path:
    """產生個人頁 profile.html，嵌入 window.__GAMES（slug→{label,cover}）供 profile.js 渲染卡片。"""
    games = {
        e["slug"]: {"label": e["label"], "cover": e.get("cover_rel") or icon_rel}
        for e in entries
    }
    games_js = ("<script>window.__GAMES="
                + json.dumps(games, ensure_ascii=False).replace("<", "\\u003c")
                + ";</script>")
    page = (
        _PROFILE_PAGE.replace("__PWAHEAD__", pwa.pwa_head(app_label, icon_rel))
        .replace("__TITLE__", _html.escape(app_label))
        .replace("__GAMES__", games_js)
    )
    out = Path(dist) / "profile.html"
    out.write_text(page, encoding="utf-8")
    return out


def write_menu(dist, app_label: str, entries, icon_rel: str = pwa.ICON_REL,
               tag_categories=None) -> Path:
    tag_categories = tag_categories or {}
    rank = {c: i for i, c in enumerate(project.CATEGORIES)}

    def cat_rank(t):
        return rank.get(tag_categories.get(t, project.DEFAULT_CATEGORY), len(rank))

    def ordered(tags):
        # 依類別順序（遊戲引擎→戰鬥系統→作者→其他）排，同類別維持原順序
        return sorted(tags, key=cat_rank)

    # 全庫不重複標籤（以小寫去重，顯示用首次出現的原文）
    tag_display = {}
    for e in entries:
        for t in (e.get("tags") or []):
            tag_display.setdefault(t.lower(), t)

    cards = []
    for e in entries:
        href = "play-" + e["slug"] + ".html"
        cover = e["cover_rel"] or icon_rel
        tags = ordered(e.get("tags") or [])
        dtags = ",".join(t.lower() for t in tags)
        card_tags = "".join(
            '<span class="tag" data-tag="' + _html.escape(t.lower(), quote=True) + '">'
            + _html.escape(t) + "</span>"
            for t in tags
        )
        card = (
            _CARD.replace("__HREF__", _html.escape(href, quote=True))
            .replace("__DLABEL__", _html.escape(e["label"].lower(), quote=True))
            .replace("__DTAGS__", _html.escape(dtags, quote=True))
            .replace("__COVER__", _html.escape(cover, quote=True))
            .replace("__CARDTAGS__", card_tags)
            .replace("__LABEL__", _html.escape(e["label"]))
        )
        cards.append(card)

    # 篩選列依固定類別分組（跳過沒有標籤的類別）
    by_cat = {c: [] for c in project.CATEGORIES}
    for key, disp in sorted(tag_display.items()):
        cat = tag_categories.get(disp)
        if cat not in by_cat:
            cat = project.DEFAULT_CATEGORY
        by_cat[cat].append((key, disp))
    groups = []
    for cat in project.CATEGORIES:
        items = by_cat[cat]
        if not items:
            continue
        buttons = "".join(
            '<button class="tagfilter" data-tag="' + _html.escape(key, quote=True) + '">'
            + _html.escape(disp) + "</button>"
            for key, disp in items)
        groups.append('<div class="taggroup"><span class="tagcat">'
                      + _html.escape(cat) + "</span>" + buttons + "</div>")
    tagfilters = "".join(groups)
    page = (
        _PAGE.replace("__PWAHEAD__", pwa.pwa_head(app_label, icon_rel))
        .replace("__TITLE__", _html.escape(app_label))
        .replace("__COUNT__", str(len(entries)))
        .replace("__TAGFILTERS__", tagfilters)
        .replace("__CARDS__", "\n".join(cards))
    )
    out = Path(dist) / "index.html"
    out.write_text(page, encoding="utf-8")
    return out
