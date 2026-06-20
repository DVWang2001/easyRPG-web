"""產生圖示網格的「遊戲庫選單」index.html（含搜尋框與點擊標籤篩選）。"""
from __future__ import annotations

import html as _html
from pathlib import Path

import project
import pwa

_PAGE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>__PWAHEAD__
<style>
* { box-sizing: border-box; }
body { margin:0; background:#111; color:#eee;
  font-family:-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif; }
header { padding:20px 16px 8px; text-align:center; font-size:20px; font-weight:600; }
.toolbar { padding:0 16px 8px; display:flex; flex-direction:column; gap:8px; }
#q { width:100%; padding:10px 12px; border-radius:12px; border:1px solid #333;
  background:#1b1b1b; color:#eee; font-size:16px; }
.tags { display:flex; flex-direction:column; gap:6px; align-items:flex-start; }
.taggroup { display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
.tagcat { color:#6b7280; font-size:12px; min-width:60px; }
.tagfilter { padding:4px 10px; border-radius:999px; border:1px solid #3a3a3a;
  background:#1f2937; color:#cbd5e1; font-size:13px; cursor:pointer; }
.tagfilter.active { background:#2563eb; color:#fff; border-color:#2563eb; }
#clear { padding:4px 10px; border-radius:999px; border:1px solid #3a3a3a;
  background:transparent; color:#9ca3af; font-size:13px; cursor:pointer; }
#empty { display:none; text-align:center; color:#888; padding:24px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(110px,1fr));
  gap:16px; padding:8px 16px 32px; }
.card { display:flex; flex-direction:column; align-items:center;
  text-decoration:none; color:inherit; -webkit-tap-highlight-color:transparent; }
.card[hidden] { display:none; }
.thumb { position:relative; width:100%; aspect-ratio:1/1; border-radius:16px;
  overflow:hidden; background:#222; box-shadow:0 2px 8px rgba(0,0,0,.5);
  transition:transform .28s cubic-bezier(.2,.7,.2,1), box-shadow .28s ease; }
.thumb img { width:100%; height:100%; object-fit:cover; display:block;
  transition:transform .45s cubic-bezier(.2,.7,.2,1); }
.thumb::after { content:""; position:absolute; inset:0; pointer-events:none;
  background:linear-gradient(115deg, transparent 30%, rgba(255,255,255,.28) 47%,
    rgba(255,255,255,.06) 55%, transparent 70%);
  transform:translateX(-120%); transition:transform .6s ease; }
.card .name { margin-top:8px; font-size:14px; text-align:center; word-break:break-word;
  transition:color .2s ease; }
/* 高質感 hover：只在真有指標懸停的裝置（手機 hover 不會卡住） */
@media (hover:hover) and (pointer:fine) {
  .card:hover .thumb { transform:translateY(-6px) scale(1.02);
    box-shadow:0 16px 30px rgba(0,0,0,.55), 0 6px 14px rgba(37,99,235,.35); }
  .card:hover .thumb img { transform:scale(1.08); }
  .card:hover .thumb::after { transform:translateX(120%); }
  .card:hover .name { color:#fff; }
}
/* 手機點到時的按壓回饋 */
.card:active .thumb { transform:scale(.96);
  box-shadow:0 6px 14px rgba(0,0,0,.5); transition:transform .1s ease; }
/* 鍵盤聚焦清楚可見 */
.card:focus-visible { outline:none; }
.card:focus-visible .thumb { box-shadow:0 0 0 3px #2563eb, 0 10px 22px rgba(0,0,0,.5); }
@media (prefers-reduced-motion:reduce) {
  .thumb, .thumb img, .thumb::after, .card .name { transition:none; }
  .card:hover .thumb::after { transform:translateX(-120%); }
}
.cardtags { text-align:center; line-height:1.6; }
.card .tag { display:inline-block; margin:4px 3px 0; padding:1px 8px; border-radius:999px;
  background:#222; color:#9ca3af; font-size:11px; cursor:pointer; }
.card .tag.active { background:#2563eb; color:#fff; }
</style>
</head>
<body>
<header>__TITLE__</header>
<div class="toolbar">
<input id="q" type="search" placeholder="搜尋遊戲或標籤…" autocomplete="off">
<div class="tags" id="tagbar">__TAGFILTERS__<button id="clear">清除篩選</button></div>
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
</body>
</html>
"""

_CARD = ('<a class="card" href="__HREF__" data-label="__DLABEL__" data-tags="__DTAGS__">'
         '<span class="thumb"><img src="__COVER__" alt=""></span>'
         '<span class="name">__LABEL__</span>'
         '<span class="cardtags">__CARDTAGS__</span></a>')


def write_menu(dist, app_label: str, entries, icon_rel: str = pwa.ICON_REL,
               tag_categories=None) -> Path:
    tag_categories = tag_categories or {}
    # 全庫不重複標籤（以小寫去重，顯示用首次出現的原文）
    tag_display = {}
    for e in entries:
        for t in (e.get("tags") or []):
            tag_display.setdefault(t.lower(), t)

    cards = []
    for e in entries:
        href = "play-" + e["slug"] + ".html"
        cover = e["cover_rel"] or icon_rel
        tags = e.get("tags") or []
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
        .replace("__TAGFILTERS__", tagfilters)
        .replace("__CARDS__", "\n".join(cards))
    )
    out = Path(dist) / "index.html"
    out.write_text(page, encoding="utf-8")
    return out
