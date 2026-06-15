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
