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
<link rel="stylesheet" href="rm-theme.css">
<style>
* { box-sizing: border-box; }
body { margin:0; min-height:100vh; color:var(--ink); }

/* 標題列＝ RM 標題畫面：皇家藍 windowskin 標題卡＋金角飾 */
header { position:relative; max-width:560px; margin:26px auto 6px; padding:18px 24px 16px;
  text-align:center; color:#fff;
  background:linear-gradient(180deg, var(--win-top), var(--win-bot));
  border:2px solid var(--win-lo); border-radius:12px;
  box-shadow: inset 0 0 0 2px rgba(220,232,255,.6), inset 0 2px 0 rgba(255,255,255,.3),
              inset 0 -3px 0 rgba(4,18,60,.5), 0 12px 30px rgba(6,9,28,.55); }
header::before, header::after { content:""; position:absolute; width:7px; height:7px; pointer-events:none;
  background:linear-gradient(var(--gold),var(--gold)) 0 0/7px 2px no-repeat,
             linear-gradient(var(--gold),var(--gold)) 0 0/2px 7px no-repeat; }
header::before { top:6px; left:6px; }
header::after { top:6px; right:6px; transform:scaleX(-1); }
.wordmark { margin:0; font-size:28px; font-weight:800; letter-spacing:.04em;
  text-shadow:0 2px 0 var(--win-lo); }
.eyebrow { margin:9px 0 0; font-size:11px;
  letter-spacing:.18em; color:var(--gold);
  display:flex; gap:10px; align-items:center; justify-content:center; }
.eyebrow .count { color:#fff; }
#me-link, #to-title { position:fixed; top:12px; z-index:5; text-decoration:none; cursor:pointer;
  padding:7px 13px; border-radius:10px; border:2px solid var(--win-lo);
  background:linear-gradient(180deg, var(--win-top), var(--win-bot)); color:#fff; font-size:13px;
  font-family:inherit; box-shadow:inset 0 0 0 1px rgba(220,232,255,.5); }
#me-link { right:12px; }
#to-title { left:12px; }
#me-link:hover, #to-title:hover { border-color:var(--gold); }

/* 工具列＝ RM 指令視窗（深色框＋斜角高光，浮在地圖上） */
.toolbar { max-width:980px; margin:10px auto 0; padding:14px 16px;
  background:rgba(10,18,44,.82); border:2px solid var(--win-lo); border-radius:12px;
  box-shadow:inset 0 0 0 2px rgba(159,180,255,.20), inset 0 1px 0 rgba(255,255,255,.12),
             0 8px 22px rgba(6,9,28,.45);
  display:flex; flex-direction:column; gap:10px; }
/* 搜尋框＝凹陷的訊息輸入欄 */
#q { width:100%; padding:11px 14px; border-radius:8px; border:2px solid var(--win-lo);
  background:#0b1330; color:var(--ink); font-size:16px;
  box-shadow:inset 0 2px 5px rgba(0,0,0,.45); }
#q::placeholder { color:var(--muted); }
#q:focus { outline:none; border-color:var(--gold);
  box-shadow:inset 0 2px 5px rgba(0,0,0,.45), 0 0 0 3px rgba(245,197,66,.22); }
.tags { display:flex; flex-direction:column; gap:6px; align-items:flex-start; }
.taggroup { display:flex; flex-wrap:wrap; gap:6px; align-items:center; }
.tagcat { color:var(--gold); font-size:12px; min-width:60px; letter-spacing:.06em; }
/* 標籤／清除＝ RM 方角指令鈕（斜角高光），選取＝金色 */
.tagfilter { padding:5px 11px; border-radius:5px; border:1px solid var(--win-lo);
  background:linear-gradient(180deg,#21305c,#131e44); color:#dbe3ff; font-size:13px; cursor:pointer;
  box-shadow:inset 0 1px 0 rgba(159,180,255,.30);
  transition:border-color .15s ease, color .15s ease; }
.tagfilter:hover { border-color:var(--gold); color:#fff; }
.tagfilter.active { background:var(--gold); color:#1a1400; border-color:var(--gold); font-weight:700;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.5); }
#clear { padding:5px 11px; border-radius:5px; border:1px solid transparent;
  background:transparent; color:var(--muted); font-size:13px; cursor:pointer; }
#clear:hover { color:var(--gold); }
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
.card::before { content:""; position:absolute; left:-13px; top:calc(50% - 24px);
  width:0; height:0; border-style:solid; border-width:6px 0 6px 10px;
  border-color:transparent transparent transparent var(--gold);
  opacity:0; transform:translateX(-7px); pointer-events:none;
  filter:drop-shadow(0 0 5px rgba(245,197,66,.6));
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

/* 開始選單（標題畫面）：載入時的 RM 指令視窗，蓋在世界地圖上 */
#titlescreen { position:fixed; inset:0; z-index:9000; display:flex;
  align-items:center; justify-content:center; padding:24px;
  background:linear-gradient(rgba(8,14,30,.42), rgba(8,14,30,.55)),
             url("overworld.png") center center / cover fixed; }
html.skip-title #titlescreen, #titlescreen[hidden] { display:none; }
.ts-window { position:relative; width:340px; max-width:100%; color:#fff;
  background:linear-gradient(180deg, var(--win-top), var(--win-bot));
  border:2px solid var(--win-lo); border-radius:12px; padding:20px 22px 16px;
  box-shadow:inset 0 0 0 2px rgba(220,232,255,.6), inset 0 2px 0 rgba(255,255,255,.3),
             inset 0 -3px 0 rgba(4,18,60,.5), 0 16px 40px rgba(6,9,28,.6); }
.ts-window::before, .ts-window::after { content:""; position:absolute; width:7px; height:7px;
  background:linear-gradient(var(--gold),var(--gold)) 0 0/7px 2px no-repeat,
             linear-gradient(var(--gold),var(--gold)) 0 0/2px 7px no-repeat; }
.ts-window::before { top:6px; left:6px; }
.ts-window::after { top:6px; right:6px; transform:scaleX(-1); }
.ts-mark { margin:6px 0 2px; font-size:26px; text-align:center; letter-spacing:.04em;
  text-shadow:0 2px 0 var(--win-lo); }
.ts-press { margin:0 0 18px; text-align:center; font-size:11px; letter-spacing:.22em; color:var(--gold); }
.ts-menu { list-style:none; margin:0; padding:0; }
.ts-row { position:relative; padding:11px 12px 11px 32px; font-size:18px; cursor:pointer; outline:none;
  border-bottom:1px solid rgba(255,255,255,.14); }
.ts-row:last-child { border-bottom:0; }
.ts-row::before { content:""; position:absolute; left:10px; top:calc(50% - 6px); width:0; height:0;
  border-style:solid; border-width:6px 0 6px 9px; border-color:transparent transparent transparent var(--gold);
  opacity:0; transform:translateX(-6px); filter:drop-shadow(0 0 5px rgba(245,197,66,.6));
  transition:opacity .12s ease, transform .12s ease; }
.ts-row[aria-current="true"]::before, .ts-row:hover::before { opacity:1; transform:translateX(0); }
.ts-row[aria-current="true"] { background:rgba(255,255,255,.12); }
.ts-blink { position:absolute; right:12px; bottom:8px; color:var(--gold); font-size:12px;
  animation:tsblink 1.05s steps(2,start) infinite; }
@keyframes tsblink { 0%,49%{opacity:1} 50%,100%{opacity:0} }
.ts-se { position:fixed; top:12px; right:12px; font-family:inherit; cursor:pointer; border-radius:8px;
  background:rgba(10,17,64,.5); color:#cdd8ff; border:1px solid var(--win-lo); padding:5px 10px; font-size:12px; }
.ts-hint { position:fixed; left:0; right:0; bottom:12px; text-align:center; color:#aeb9ee;
  font-size:11px; letter-spacing:.08em; }
/* 關於：小型 RM 訊息窗 */
#ts-about { position:fixed; inset:0; z-index:9500; }
#ts-about[hidden] { display:none; }
.ts-about-bd { position:absolute; inset:0; background:rgba(6,9,28,.66); }
.ts-about-dlg { position:relative; max-width:380px; margin:14vh auto; color:#eaf0ff;
  background:var(--panel); border:1px solid var(--win-lo); border-radius:14px; padding:18px 18px 16px;
  box-shadow:inset 0 0 0 1px rgba(159,180,255,.3), 0 14px 44px rgba(6,9,28,.7); }
.ts-about-dlg h3 { margin:2px 0 10px; font-size:16px; }
.ts-about-dlg p { margin:0; line-height:1.8; font-size:14px;
  font-family:-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif; }
.ts-about-close { position:absolute; top:10px; right:12px; cursor:pointer; border-radius:7px;
  background:rgba(10,17,64,.45); color:#cdd8ff; border:1px solid var(--win-lo); padding:4px 9px; font-size:12px; }
.ts-about-close:hover { color:var(--gold); border-color:var(--gold); }
@media (prefers-reduced-motion:reduce) { .ts-blink{animation:none} .ts-row::before{transition:none} }
</style>
<link rel="stylesheet" href="favorites.css">
<link rel="stylesheet" href="popular.css">
<link rel="stylesheet" href="announce.css">
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.8/dist/purify.min.js"></script>
<script>try{if(sessionStorage.getItem('ep-booted'))document.documentElement.classList.add('skip-title');}catch(e){}</script>
</head>
<body>
<div id="titlescreen">
<div class="ts-window">
<h1 class="ts-mark">__TITLE__</h1>
<p class="ts-press">PRESS START</p>
<ul class="ts-menu" role="menu">
<li class="ts-row" tabindex="0" role="menuitem" data-act="start" aria-current="true">開始遊戲</li>
<li class="ts-row" tabindex="0" role="menuitem" data-act="favs">我的收藏</li>
<li class="ts-row" tabindex="0" role="menuitem" data-act="news">公告</li>
<li class="ts-row" tabindex="0" role="menuitem" data-act="about">關於</li>
</ul>
<span class="ts-blink">▼</span>
</div>
<button class="ts-se" id="ts-se" type="button">🔇 音效</button>
<p class="ts-hint">↑↓ 移動游標　Enter 決定　（滑鼠亦可）</p>
</div>
<div id="ts-about" hidden>
<div class="ts-about-bd"></div>
<div class="ts-about-dlg">
<button class="ts-about-close" type="button">✕ 返回 (Esc)</button>
<h3>關於</h3>
<p>__TITLE__ — 用瀏覽器直接遊玩的 RPG Maker 2000／2003 作品庫，由 EasyRPG Player 驅動。選一款遊戲即可開始；進度可存雲端，並能留言、評分、寫攻略。</p>
</div>
</div>
<button id="to-title" type="button">≡ 選單</button>
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
/* 開始選單：鍵盤 ▶ 導航＋RM 音效（預設關），每個分頁只出現一次（ep-booted） */
(function(){
  var ts = document.getElementById('titlescreen');
  if (!ts) return;
  var rows = Array.prototype.slice.call(ts.querySelectorAll('.ts-row'));
  var about = document.getElementById('ts-about');
  var i = 0;
  var seOn = false, ac;
  function beep(f, d){ if(!seOn) return; try{
    ac = ac || new (window.AudioContext||window.webkitAudioContext)();
    var o=ac.createOscillator(), g=ac.createGain(); o.type='square'; o.frequency.value=f;
    o.connect(g); g.connect(ac.destination); g.gain.value=.04; o.start(); o.stop(ac.currentTime+(d||.05));
  }catch(e){} }
  var seb = document.getElementById('ts-se');
  if (seb) seb.onclick = function(){ seOn=!seOn; seb.textContent = seOn?'🔊 音效':'🔇 音效'; if(seOn) beep(880); };
  function move(n){ rows[i].setAttribute('aria-current','false'); i=(n+rows.length)%rows.length;
    rows[i].setAttribute('aria-current','true'); rows[i].focus(); beep(660); }
  function boot(){ try{ sessionStorage.setItem('ep-booted','1'); }catch(e){} }
  function hide(){ ts.hidden=true; }
  function show(){ document.documentElement.classList.remove('skip-title'); ts.hidden=false;
    i=0; rows.forEach(function(r){ r.setAttribute('aria-current','false'); });
    rows[0].setAttribute('aria-current','true'); rows[0].focus(); }
  function decide(){ beep(1040,.12); var act=rows[i].getAttribute('data-act');
    if (act==='start'){ boot(); hide(); }
    else if (act==='favs'){ boot(); location.href='profile.html'; }
    else if (act==='news'){ boot(); hide();
      var a=document.getElementById('announce'); if(a && !a.hidden) a.scrollIntoView({behavior:'smooth'}); }
    else if (act==='about'){ if(about) about.hidden=false; }
  }
  // 遊戲庫左上「≡ 選單」鈕：回上一層（標題畫面）
  var back=document.getElementById('to-title');
  if (back) back.onclick=show;
  ts.addEventListener('keydown', function(e){
    if (e.key==='ArrowDown'){ e.preventDefault(); move(i+1); }
    else if (e.key==='ArrowUp'){ e.preventDefault(); move(i-1); }
    else if (e.key==='Enter'){ e.preventDefault(); decide(); }
  });
  rows.forEach(function(r,n){
    r.addEventListener('mouseenter', function(){ rows[i].setAttribute('aria-current','false'); i=n; r.setAttribute('aria-current','true'); });
    r.addEventListener('click', decide);
  });
  if (about){
    var bd=about.querySelector('.ts-about-bd'), cl=about.querySelector('.ts-about-close');
    function closeA(){ about.hidden=true; rows[i].focus(); beep(360,.12); }
    if (bd) bd.onclick=closeA; if (cl) cl.onclick=closeA;
    document.addEventListener('keydown', function(e){ if(e.key==='Escape' && !about.hidden){ e.preventDefault(); closeA(); } });
  }
  rows[0].focus();
})();
</script>
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
<link rel="stylesheet" href="rm-theme.css">
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
