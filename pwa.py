"""PWA 外殼：圖示、manifest、service worker、改寫 index.html。"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ICON_REL = "icons/icon.png"


def install_icon(dist, icon_path) -> str:
    dist = Path(dist)
    target = dist / ICON_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(icon_path), target)
    return ICON_REL


def write_manifest(dist, app_label: str, icon_rel: str = ICON_REL) -> Path:
    dist = Path(dist)
    manifest = {
        "name": app_label,
        "short_name": app_label,
        "start_url": ".",
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
    out = dist / "manifest.webmanifest"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


SW_TEMPLATE = """\
// 由 easyrpg_web_build 產生：全資產 precache + cache-first，安裝後可完全離線。
const CACHE = 'easyrpg-web-v1';
const PRECACHE = %s;

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
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
    caches.match(e.request).then((hit) =>
      hit || fetch(e.request).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
        return res;
      }).catch(() => caches.match('index.html'))
    )
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


def inject_play_game_info(dist, entries) -> Path:
    """把 slug→{name,cover?} 對照表與切換 script 注入 dist/play.html。
    載入時依 ?game=<slug> 設定 document.title 與 favicon（封面載入成功才換）。"""
    dist = Path(dist)
    play = dist / "play.html"
    games = {}
    for e in entries:
        info = {"name": e["label"]}
        if e.get("cover_rel"):
            info["cover"] = e["cover_rel"]
        games[e["slug"]] = info
    # ensure_ascii=False 保留中文；把 < 轉成 < 以防名稱含 </script> 破壞標籤
    data = json.dumps(games, ensure_ascii=False).replace("<", "\\u003c")
    script = (
        "\n<script>\n"
        "window.__EASYRPG_GAMES__ = " + data + ";\n"
        "(function(){"
        "var slug=new URLSearchParams(location.search).get('game');"
        "if(!slug)return;"
        "var info=window.__EASYRPG_GAMES__[slug];"
        "if(!info)return;"
        "if(info.name)document.title=info.name;"
        "if(info.cover){var img=new Image();img.onload=function(){"
        "var link=document.querySelector(\"link[rel~='icon']\")||document.createElement('link');"
        "link.setAttribute('rel','icon');link.setAttribute('href',info.cover);"
        "document.head.appendChild(link);};img.src=info.cover;}"
        "})();\n"
        "</script>\n"
    )
    html = play.read_text(encoding="utf-8")
    if "</head>" in html:
        html = html.replace("</head>", script + "</head>", 1)
    elif "</body>" in html:
        html = html.replace("</body>", script + "</body>", 1)
    else:
        html = html + script
    play.write_text(html, encoding="utf-8")
    return play
