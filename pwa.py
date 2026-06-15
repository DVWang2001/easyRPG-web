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
