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


def _build_manifest(name: str, start_url: str, icon_rel: str) -> dict:
    return {
        "name": name,
        "short_name": name,
        "start_url": start_url,
        "scope": ".",
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
// 由 easyrpg_web_build 產生：逐檔 precache（回報進度）+ cache-first，全部下載後可離線。
const CACHE = 'easyrpg-web-v1';
const PRECACHE = %s;

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    const total = PRECACHE.length;
    let done = 0, idx = 0;
    async function notify() {
      const cls = await self.clients.matchAll({ includeUncontrolled: true });
      for (const cl of cls) cl.postMessage({ type: 'precache', done: done, total: total });
    }
    await notify();
    // 限併發下載：同時 N 個（比逐檔快很多，又不會上百個一起塞爆頻寬），
    // 容錯（單檔失敗不中斷），每檔回報進度。
    async function worker() {
      while (idx < total) {
        const u = PRECACHE[idx++];
        try { await c.add(u); } catch (err) {}
        done++;
        notify();
      }
    }
    const CONCURRENCY = 6;
    await Promise.all(Array.from({ length: Math.min(CONCURRENCY, total) }, worker));
    await notify();
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then((hit) => {
      if (hit) return hit;
      return fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      }).catch(() => {
        // 離線且未快取：導航請求退回殼頁；素材請求回傳錯誤（不要拿 HTML 冒充素材）
        if (e.request.mode === 'navigate') return caches.match('index.html');
        return Response.error();
      });
    })
  );
});
"""


def _precache_list(dist: Path) -> list:
    files = []
    for p in sorted(dist.rglob("*")):
        if p.is_file() and p.name != "service-worker.js":
            files.append(p.relative_to(dist).as_posix())
    return files


def write_service_worker(dist) -> Path:
    dist = Path(dist)
    files = _precache_list(dist)
    out = dist / "service-worker.js"
    out.write_text(SW_TEMPLATE % json.dumps(files, ensure_ascii=False), encoding="utf-8")
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
        cover = e.get("cover_rel") or icon_rel
        cover_esc = _html.escape(cover, quote=True)
        title_esc = _html.escape(label, quote=True)
        manifest_name = "manifest-" + slug + ".webmanifest"
        # 每遊戲 manifest：icons＝封面、start_url＝該遊戲頁 → 加入主畫面得到該遊戲圖示/名稱
        (dist / manifest_name).write_text(
            json.dumps(
                _build_manifest(label, "play-" + slug + ".html", cover),
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        # 鎖住 document.title 用的 JS 字串字面值（防 </script> 注入）
        title_js = json.dumps(label).replace("<", "\\u003c")
        html = template.replace("game: undefined", "game: " + json.dumps(slug))
        # 移除模板繼承的整庫 tag，避免 iOS 採用庫圖示
        html = re.sub(r'<link[^>]*rel="manifest"[^>]*>', "", html, count=1, flags=re.S)
        html = re.sub(r'<link[^>]*rel="apple-touch-icon"[^>]*>', "", html, count=1, flags=re.S)
        html = re.sub(r'<meta[^>]*name="apple-mobile-web-app-title"[^>]*>', "", html, count=1, flags=re.S)
        html = re.sub(r"<title>.*?</title>", "", html, count=1, flags=re.S)
        new_head = (
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
        (dist / ("play-" + slug + ".html")).write_text(html, encoding="utf-8")
