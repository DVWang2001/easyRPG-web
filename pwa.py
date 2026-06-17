"""PWA 外殼：圖示、manifest、service worker、改寫 index.html。"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ICON_REL = "icons/icon.png"


def install_icon(dist, icon_path) -> str:
    dist = Path(dist)
    target = dist / ICON_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(icon_path), target)
    return ICON_REL


def _build_manifest(
    name: str, start_url: str, icon_rel: str, scope: str = ".", app_id: str | None = None
) -> dict:
    return {
        "name": name,
        "short_name": name,
        # id 決定 Android Chrome 眼中的 App 身分；預設＝start_url（與 Chrome 自動推算一致、且穩定）。
        "id": app_id or start_url,
        "start_url": start_url,
        # scope 決定 App「範圍」；每遊戲收窄到自己的頁，避免裝了一個就被視為已涵蓋其他遊戲。
        "scope": scope,
        "display": "standalone",
        "orientation": "landscape",
        "background_color": "#000000",
        "theme_color": "#000000",
        "icons": [
            {"src": icon_rel, "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": icon_rel, "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": icon_rel, "sizes": "180x180", "type": "image/png"},
        ],
    }


def write_manifest(dist, app_label: str, icon_rel: str = ICON_REL) -> Path:
    dist = Path(dist)
    out = dist / "manifest.webmanifest"
    out.write_text(
        json.dumps(_build_manifest(app_label, ".", icon_rel), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out


SW_TEMPLATE = """\
// 由 easyrpg_web_build 產生：
//   遊戲大檔（games/ 底下）→ cache-first（離線下載保留，幾乎不變）。
//   外殼（HTML/JS/WASM/manifest 等）→ network-first（線上永遠拿最新 → 部署即生效；離線退回快取）。
// 「下載某個遊戲以供離線」由各遊戲頁自己處理（見 precache-<slug>.json），快取進 easyrpg-games。
const CACHE = 'easyrpg-games';

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      // 清掉舊版（含早期 easyrpg-web-v* 全庫快取），只保留 easyrpg-games
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// 路徑含 /games/ 視為遊戲大檔（cache-first）；其餘為外殼（network-first）。
function isGameAsset(req) {
  try { return new URL(req.url).pathname.includes('/games/'); }
  catch (err) { return false; }
}

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  if (isGameAsset(e.request)) {
    // 遊戲資料：cache-first（離線下載優先用快取，沒有才抓網路並快取）
    e.respondWith(
      caches.match(e.request).then((hit) => {
        if (hit) return hit;
        return fetch(e.request).then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
          return res;
        });
      })
    );
  } else {
    // 外殼：network-first（線上拿最新並更新快取；離線退回快取，導航退回殼頁）
    e.respondWith(
      fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      }).catch(() =>
        caches.match(e.request).then((hit) => {
          if (hit) return hit;
          if (e.request.mode === 'navigate') return caches.match('index.html');
          return Response.error();
        })
      )
    );
  }
});
"""


def write_service_worker(dist) -> Path:
    dist = Path(dist)
    out = dist / "service-worker.js"
    out.write_text(SW_TEMPLATE, encoding="utf-8")
    return out


import html as _html


def pwa_head(app_label: str, icon_rel: str) -> str:
    title = _html.escape(app_label)
    return (
        '\n<link rel="manifest" href="manifest.webmanifest">'
        f'\n<link rel="apple-touch-icon" href="{icon_rel}">'
        '\n<meta name="apple-mobile-web-app-capable" content="yes">'
        '\n<meta name="apple-mobile-web-app-status-bar-style" content="black">'
        f'\n<meta name="apple-mobile-web-app-title" content="{title}">'
        '\n<meta name="theme-color" content="#000000">'
        '\n<meta name="viewport" content="width=device-width, initial-scale=1, '
        'viewport-fit=cover, user-scalable=no">'
        '\n<script>'
        "if('serviceWorker' in navigator){"
        "window.addEventListener('load',function(){"
        "navigator.serviceWorker.register('service-worker.js');});}"
        '</script>\n'
    )


def patch_index_html(dist, app_label: str, icon_rel: str = ICON_REL) -> Path:
    dist = Path(dist)
    index = dist / "index.html"
    html = index.read_text(encoding="utf-8")
    snippet = pwa_head(app_label, icon_rel)
    if "</head>" in html:
        html = html.replace("</head>", snippet + "</head>", 1)
    elif "</body>" in html:
        html = html.replace("</body>", snippet + "</body>", 1)
    else:
        html = html + snippet
    index.write_text(html, encoding="utf-8")
    return index



def write_game_pages(dist, entries, icon_rel=ICON_REL) -> None:
    """以 dist/play.html 為模板，為每個遊戲產出 play-<slug>.html 與其專屬 manifest。

    每個遊戲頁：靜態 <title>＝遊戲名、<link rel=icon>/apple-touch-icon＝封面、
    自己的 <link rel=manifest>（icons＝封面、name＝遊戲名、start_url＝該頁），並 baked-in game。
    模板繼承的整庫 manifest / apple-touch-icon / app-title 會先被移除，
    讓 iOS「加入主畫面」用的是該遊戲封面（而非遊戲庫主圖示）。"""
    dist = Path(dist)
    template = (dist / "play.html").read_text(encoding="utf-8")
    for e in entries:
        slug = e["slug"]
        label = e["label"]
        # 自訂取名字表的遊戲載入 player-custom/ 引擎；其餘用根目錄官方引擎。
        engine = "player-custom/" if e.get("custom") else ""
        cover = e.get("cover_rel") or icon_rel
        cover_esc = _html.escape(cover, quote=True)
        title_esc = _html.escape(label, quote=True)
        manifest_name = "manifest-" + slug + ".webmanifest"
        # 每遊戲 manifest：icons＝封面、start_url＝該遊戲頁 → 加入主畫面得到該遊戲圖示/名稱。
        # scope/id 收窄到該遊戲頁，讓 Android Chrome 視各遊戲為獨立 App（否則裝一個就裝不了其他）。
        page_url = "play-" + slug + ".html"
        (dist / manifest_name).write_text(
            json.dumps(
                _build_manifest(label, page_url, cover, scope=page_url),
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        # 該遊戲的離線下載清單（殼 + 這個遊戲的所有檔），供遊戲頁自己下載
        game_dir = dist / "games" / slug
        game_files = (
            sorted(
                p.relative_to(dist).as_posix()
                for p in game_dir.rglob("*")
                if p.is_file()
            )
            if game_dir.exists()
            else []
        )
        shell = [engine + "index.js", engine + "index.wasm",
                 "play-" + slug + ".html", manifest_name, icon_rel]
        (dist / ("precache-" + slug + ".json")).write_text(
            json.dumps(shell + game_files, ensure_ascii=False), encoding="utf-8"
        )
        # 鎖住 document.title 用的 JS 字串字面值（防 </script> 注入）
        title_js = json.dumps(label).replace("<", "\\u003c")
        tmpl = (template.replace('src="index.js"', 'src="' + engine + 'index.js"')
                if engine else template)
        html = tmpl.replace("game: undefined", "game: " + json.dumps(slug))
        # 移除模板繼承的整庫 tag，避免 iOS 採用庫圖示
        html = re.sub(r'<link[^>]*rel="manifest"[^>]*>', "", html, count=1, flags=re.S)
        html = re.sub(r'<link[^>]*rel="apple-touch-icon"[^>]*>', "", html, count=1, flags=re.S)
        html = re.sub(r'<meta[^>]*name="apple-mobile-web-app-title"[^>]*>', "", html, count=1, flags=re.S)
        html = re.sub(r"<title>.*?</title>", "", html, count=1, flags=re.S)
        # 自訂(SDL3)引擎會把 canvas 內聯尺寸設成遊戲解析度(很小);用 !important 強制撐滿
        # (官方 SDL2 shell 沒這段 → SDL3 在此 shell 下會「畫面小、黑邊大」)。
        canvas_fix = ("\n<style>#canvas{width:100vw !important;height:100vh !important}</style>"
                      if engine else "")
        new_head = (
            canvas_fix +
            "\n<title>" + title_esc + "</title>"
            '\n<meta name="apple-mobile-web-app-title" content="' + title_esc + '">'
            '\n<link rel="icon" href="' + cover_esc + '">'
            '\n<link rel="apple-touch-icon" href="' + cover_esc + '">'
            '\n<link rel="manifest" href="' + manifest_name + '">'
            # 鎖標題：EasyRPG 引擎載入後會把 document.title 改成遊戲內建標題（可能是 untitled），
            # 這裡把 title 鎖成導入的名稱，讓 iOS「加入主畫面」讀到正確名稱。
            "\n<script>(function(){var t=" + title_js + ";"
            "try{Object.defineProperty(document,'title',{configurable:true,"
            "get:function(){return t;},set:function(){}});}catch(e){}"
            "document.title=t;"
            "if(window.MutationObserver){var el=document.querySelector('title');"
            "if(el){new MutationObserver(function(){if(document.title!==t){document.title=t;}})"
            ".observe(el,{childList:true,characterData:true,subtree:true});}}})();</script>\n"
        )
        html = html.replace("</head>", new_head + "</head>", 1)
        # 只下載這一個遊戲的進度條：載入時抓 precache-<slug>.json，逐檔快取進 easyrpg-games
        slug_js = json.dumps(slug)
        dl_snippet = (
            "\n<style>#dl{position:fixed;left:0;right:0;bottom:0;background:#1f2937;"
            "padding:8px 14px calc(8px + env(safe-area-inset-bottom));"
            "font:13px -apple-system,sans-serif;color:#cbd5e1;z-index:9999}"
            "#dltrack{height:5px;background:#374151;border-radius:3px;overflow:hidden}"
            "#dlbar{height:100%;width:0;background:#2563eb;transition:width .2s}"
            "#dltext{display:block;margin-top:5px}</style>"
            '\n<div id="dl" hidden><div id="dltrack"><div id="dlbar"></div></div><span id="dltext"></span></div>'
            '\n<script>(function(){if(!("caches" in window))return;var SLUG=' + slug_js + ";"
            'fetch("precache-"+SLUG+".json").then(function(r){return r.json();}).then(function(files){'
            'var box=document.getElementById("dl"),bar=document.getElementById("dlbar"),'
            'txt=document.getElementById("dltext");'
            'caches.open("easyrpg-games").then(function(cache){'
            "var total=files.length,done=0,idx=0;"
            'function show(){box.hidden=false;var pct=total?Math.round(done/total*100):100;'
            'bar.style.width=pct+"%";'
            'if(done>=total){txt.textContent="✓ 此遊戲已可離線";'
            "setTimeout(function(){box.hidden=true;},3000);}"
            'else{txt.textContent="下載此遊戲以供離線… "+pct+"% ("+done+"/"+total+")";}}'
            "show();"
            "function worker(){return (async function(){while(idx<total){var f=files[idx++];"
            "try{if(!(await cache.match(f)))await cache.add(f);}catch(e){}done++;show();}})();}"
            "var n=Math.min(6,total)||1,ws=[];for(var i=0;i<n;i++)ws.push(worker());"
            "Promise.all(ws);});}).catch(function(){});})();</script>\n"
        )
        if "</body>" in html:
            html = html.replace("</body>", dl_snippet + "</body>", 1)
        else:
            html = html + dl_snippet
        (dist / ("play-" + slug + ".html")).write_text(html, encoding="utf-8")
