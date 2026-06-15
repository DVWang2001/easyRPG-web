# easyRPG-web (RPG Maker → iOS 網頁版/PWA) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在純 Windows 上，把一個 RPG Maker 2000/2003 遊戲資料夾打包成自包含的靜態網頁/PWA，部署到 GitHub Pages 後 iPhone 用 Safari「加入主畫面」即可離線遊玩，並附 Tkinter GUI。

**Architecture:** 不編譯。下載 EasyRPG 官方預編 web player（WASM）→ 把遊戲 staging 進 `dist/games/default/`（套排除規則、注入 Windows 音色 SF2、選灌 RTP）→ 用純 Python 重寫的 gencache 產生 `index.json` → 鋪 PWA 外殼（manifest + 全資產 precache 的 service worker + 圖示，並改寫 player 的 `index.html`）→ 產出 `dist/`，可本機 `http.server` 測試或一鍵 push 到 `gh-pages`。CLI 核心 `easyrpg_web_build.py`，GUI `easyrpg_web_gui.py` 是其薄前端。

**Tech Stack:** Python 3.8+（僅標準庫：`argparse`/`urllib`/`tarfile`/`json`/`unicodedata`/`shutil`/`pathlib`/`tkinter`）；pytest（開發測試）；git/gh（部署）。刻意零第三方執行期依賴。

**Spec:** `docs/superpowers/specs/2026-06-15-easyrpg-web-ios-pwa-design.md`

**專案根目錄：** `C:\opensource\easyRPG-web\`（與既有 Android apk builder `C:\opensource\easyRPG` 完全分開）

---

## 檔案結構

| 檔案 | 職責 |
|---|---|
| `gencache.py` | 純 Python 重寫官方 gencache：遞迴掃遊戲夾 → `index.json`（純函式、可測） |
| `player_fetch.py` | 下載/快取/解壓官方預編 web player |
| `staging.py` | 複製遊戲（套排除）、注入 SF2、選灌 RTP |
| `pwa.py` | 產生 manifest、service worker（全資產 precache）、安裝圖示、改寫 `index.html` |
| `deploy.py` | 把 `dist/` push 到 `gh-pages` |
| `easyrpg_web_build.py` | CLI 核心 orchestrator：串起上述全部 |
| `easyrpg_web_gui.py` | Tkinter GUI（薄前端，`import easyrpg_web_build as core`） |
| `assets/easyrpg.soundfont` | 內附 Windows 音色（從既有專案複製） |
| `assets/app_icon.png` | 內附預設圖示（從既有專案複製） |
| `啟動GUI.bat` / `啟動.bat` / `run.sh` / `README.md` | 啟動器與說明 |
| `tests/…` | pytest 測試 |
| `.gitignore` | 忽略 `dist/`、`.player-cache/`、`__pycache__/` |

---

### Task 1: 專案骨架與內附資產

**Files:**
- Create: `.gitignore`
- Create: `assets/easyrpg.soundfont`（從 `C:\opensource\easyRPG\soundfont\easyrpg.soundfont` 複製）
- Create: `assets/app_icon.png`（從 `C:\opensource\easyRPG\app_icon.png` 複製）
- Create: `tests/__init__.py`（空檔）
- Create: `pytest.ini`

- [ ] **Step 1: 建 `.gitignore`**

```gitignore
__pycache__/
*.pyc
dist/
.player-cache/
.gh-pages-worktree/
.pytest_cache/
```

- [ ] **Step 2: 建 `pytest.ini`**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

- [ ] **Step 3: 複製內附資產（在 `C:\opensource\easyRPG-web`）**

```bash
mkdir -p assets tests
cp /c/opensource/easyRPG/soundfont/easyrpg.soundfont assets/easyrpg.soundfont
cp /c/opensource/easyRPG/app_icon.png assets/app_icon.png
: > tests/__init__.py
```

- [ ] **Step 4: 驗證**

Run: `ls -lh assets/`
Expected: 看到 `easyrpg.soundfont`（約 3.1M）與 `app_icon.png`（約 5.5K）。

- [ ] **Step 5: Commit**

```bash
git add .gitignore pytest.ini assets/ tests/__init__.py
git commit -m "chore: 專案骨架與內附音色/圖示資產"
```

---

### Task 2: `gencache.py` —— 純 Python 重寫 gencache

依官方 `EasyRPG/Tools/gencache/src/main.cpp` 行為：key = NFKC-normalised lowercase；根層與 `.ini`/`.po` 保留副檔名，其餘 key 去副檔名；每個子目錄帶 `_dirname`（原始大小寫）；`exfont` 特例；遞迴深度預設 4；輸出 `{"metadata":{"version":2,"date":...},"cache":{...}}`。

**Files:**
- Create: `gencache.py`
- Test: `tests/test_gencache.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_gencache.py
import json
from pathlib import Path

import gencache


def _make_game(root: Path):
    (root / "RPG_RT.ldb").write_text("x")
    (root / "RPG_RT.lmt").write_text("x")
    (root / "easyrpg.soundfont").write_bytes(b"SF2")
    cs = root / "CharSet"
    cs.mkdir()
    (cs / "Hero.png").write_bytes(b"png")
    cfg = root / "Config"
    cfg.mkdir()
    (cfg / "settings.ini").write_text("a=b")


def test_root_files_keep_extension(tmp_path):
    _make_game(tmp_path)
    cache = gencache.generate_index(tmp_path)["cache"]
    # 根層保留副檔名：key 是小寫全名，value 是原始大小寫全名
    assert cache["rpg_rt.ldb"] == "RPG_RT.ldb"
    assert cache["easyrpg.soundfont"] == "easyrpg.soundfont"


def test_subdir_strips_extension_and_has_dirname(tmp_path):
    _make_game(tmp_path)
    cache = gencache.generate_index(tmp_path)["cache"]
    charset = cache["charset"]
    assert charset["_dirname"] == "CharSet"      # 原始大小寫
    assert charset["hero"] == "Hero.png"          # 去副檔名 key，原名 value


def test_ini_keeps_extension_in_subdir(tmp_path):
    _make_game(tmp_path)
    cache = gencache.generate_index(tmp_path)["cache"]
    assert cache["config"]["settings.ini"] == "settings.ini"


def test_metadata_version_2(tmp_path):
    _make_game(tmp_path)
    meta = gencache.generate_index(tmp_path)["metadata"]
    assert meta["version"] == 2
    assert len(meta["date"]) == 10  # YYYY-MM-DD


def test_write_index_writes_utf8_json(tmp_path):
    _make_game(tmp_path)
    out = gencache.write_index(tmp_path)
    assert out == tmp_path / "index.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["metadata"]["version"] == 2
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_gencache.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'gencache'`）

- [ ] **Step 3: 實作 `gencache.py`**

```python
# gencache.py
"""純 Python 重寫 EasyRPG 的 gencache 工具。

EasyRPG web player 需要 index.json，因為 RPG Maker 遊戲引用檔案時不帶副檔名。
本實作忠於 EasyRPG/Tools gencache (src/main.cpp)：NFKC-normalised 小寫 key、
除根層與 .ini/.po 外去副檔名、每個子目錄帶 _dirname、exfont 特例、metadata version 2。
"""
from __future__ import annotations

import json
import os
import unicodedata
from datetime import date
from pathlib import Path

KEEP_EXTENSION = (".ini", ".po")
DEFAULT_DEPTH = 4


def _norm(name: str) -> str:
    # C++ 是 ICU toLower(root locale) 後 NFKC normalize。
    return unicodedata.normalize("NFKC", name.lower())


def _strip_ext(name: str) -> str:
    dot = name.rfind(".")
    return name if dot < 0 else name[:dot]


def _keep_extension(lower_name: str) -> bool:
    return lower_name.endswith(KEEP_EXTENSION)


def _walk(path: Path, depth: int, first: bool = False) -> dict:
    if depth == 0:
        return {}
    try:
        entries = list(os.scandir(path))
    except OSError:
        return {}
    result: dict = {}
    if not first:
        result["_dirname"] = path.name
    for entry in entries:
        original = entry.name
        if original == "_dirname":
            continue
        lower = _norm(original)
        if entry.is_dir():
            sub = _walk(Path(entry.path), depth - 1)
            if sub:
                result[lower] = sub
        elif entry.is_file():
            if first or _keep_extension(lower):
                key = "exfont" if _strip_ext(lower) == "exfont" else lower
                result[key] = original
            else:
                result[_strip_ext(lower)] = original
    return result


def generate_index(game_dir, depth: int = DEFAULT_DEPTH) -> dict:
    cache = _walk(Path(game_dir), depth, first=True)
    return {
        "metadata": {"version": 2, "date": date.today().isoformat()},
        "cache": cache,
    }


def write_index(game_dir, output=None, depth: int = DEFAULT_DEPTH) -> Path:
    game_dir = Path(game_dir)
    output = Path(output) if output else game_dir / "index.json"
    data = generate_index(game_dir, depth)
    output.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    return output


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print("written:", write_index(target))
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_gencache.py -v`
Expected: PASS（5 passed）

- [ ] **Step 5: Commit**

```bash
git add gencache.py tests/test_gencache.py
git commit -m "feat: 純 Python gencache（產生 EasyRPG web player 的 index.json）"
```

---

### Task 3: `player_fetch.py` —— 下載/快取官方預編 web player

**Files:**
- Create: `player_fetch.py`
- Test: `tests/test_player_fetch.py`

- [ ] **Step 1: 寫失敗測試（用本地 tar.gz 當假 player，免真連網）**

```python
# tests/test_player_fetch.py
import io
import tarfile
from pathlib import Path

import player_fetch


def _make_fake_player_tarball(path: Path):
    """打包成內含 index.html/index.js/index.wasm/games 的 tar.gz。"""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in [
            ("index.html", b"<html></html>"),
            ("index.js", b"// js"),
            ("index.wasm", b"\0asm"),
            ("games/default/.keep", b""),
        ]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    path.write_bytes(buf.getvalue())


def test_ensure_player_extracts_and_returns_dir(tmp_path):
    tarball = tmp_path / "fake.tar.gz"
    _make_fake_player_tarball(tarball)
    cache = tmp_path / "cache"
    url = tarball.resolve().as_uri()  # file:// URL

    player_dir = player_fetch.ensure_player(cache, url=url)

    assert (player_dir / "index.wasm").exists()
    assert (player_dir / "index.js").exists()
    assert (player_dir / "index.html").exists()


def test_ensure_player_uses_cache_second_time(tmp_path):
    tarball = tmp_path / "fake.tar.gz"
    _make_fake_player_tarball(tarball)
    cache = tmp_path / "cache"
    url = tarball.resolve().as_uri()

    player_fetch.ensure_player(cache, url=url)
    tarball.unlink()  # 刪掉來源，第二次必須走快取
    player_dir = player_fetch.ensure_player(cache, url=url)
    assert (player_dir / "index.wasm").exists()
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_player_fetch.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'player_fetch'`）

- [ ] **Step 3: 實作 `player_fetch.py`**

```python
# player_fetch.py
"""下載、快取並解壓 EasyRPG 官方預編 web player（WASM）。"""
from __future__ import annotations

import shutil
import tarfile
import urllib.request
from pathlib import Path

PLAYER_URL = "https://easyrpg.org/downloads/player/latest/easyrpg-player-latest-js.tar.gz"


def _find_player_root(extracted: Path) -> Path:
    """回傳含 index.wasm 的目錄（tarball 可能多包一層）。"""
    for wasm in extracted.rglob("index.wasm"):
        return wasm.parent
    raise FileNotFoundError("解壓後找不到 index.wasm，下載的 player 格式可能變了。")


def ensure_player(cache_dir, url: str = PLAYER_URL, refresh: bool = False) -> Path:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    tarball = cache_dir / "easyrpg-player-latest-js.tar.gz"
    extracted = cache_dir / "player"

    if refresh:
        if tarball.exists():
            tarball.unlink()
        if extracted.exists():
            shutil.rmtree(extracted)

    if not tarball.exists():
        urllib.request.urlretrieve(url, tarball)

    if not extracted.exists():
        extracted.mkdir(parents=True)
        with tarfile.open(tarball, "r:gz") as tar:
            tar.extractall(extracted)

    return _find_player_root(extracted)
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_player_fetch.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add player_fetch.py tests/test_player_fetch.py
git commit -m "feat: 下載/快取 EasyRPG 官方預編 web player"
```

---

### Task 4: `staging.py` —— 複製遊戲（排除）、注入 SF2、灌 RTP

**Files:**
- Create: `staging.py`
- Test: `tests/test_staging.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_staging.py
from pathlib import Path

import staging


def _make_game(root: Path):
    (root / "RPG_RT.ldb").write_text("game")
    (root / "notes.bak").write_text("junk")
    (root / "patch.trans").write_text("junk")
    sub = root / "CharSet"
    sub.mkdir()
    (sub / "Hero.png").write_bytes(b"png")


def test_stage_copies_game_and_skips_default_ignores(tmp_path):
    game = tmp_path / "game"
    game.mkdir()
    _make_game(game)
    dest = tmp_path / "dest"

    staging.stage_game(game, dest)

    assert (dest / "RPG_RT.ldb").exists()
    assert (dest / "CharSet" / "Hero.png").exists()
    assert not (dest / "notes.bak").exists()
    assert not (dest / "patch.trans").exists()


def test_stage_injects_soundfont(tmp_path):
    game = tmp_path / "game"
    game.mkdir()
    _make_game(game)
    sf = tmp_path / "win.sf2"
    sf.write_bytes(b"RIFFsfbk")
    dest = tmp_path / "dest"

    staging.stage_game(game, dest, soundfont=sf)

    assert (dest / "easyrpg.soundfont").read_bytes() == b"RIFFsfbk"


def test_stage_rtp_then_game_overrides(tmp_path):
    rtp = tmp_path / "rtp"
    rtp.mkdir()
    (rtp / "shared.png").write_text("from-rtp")
    (rtp / "RPG_RT.ldb").write_text("rtp-version")
    game = tmp_path / "game"
    game.mkdir()
    (game / "RPG_RT.ldb").write_text("game-version")
    dest = tmp_path / "dest"

    staging.stage_game(game, dest, rtp=rtp)

    assert (dest / "shared.png").read_text() == "from-rtp"       # RTP 補進來
    assert (dest / "RPG_RT.ldb").read_text() == "game-version"   # 遊戲覆蓋 RTP


def test_stage_custom_exclude_path(tmp_path):
    game = tmp_path / "game"
    game.mkdir()
    _make_game(game)
    dest = tmp_path / "dest"

    staging.stage_game(game, dest, exclude_paths=["CharSet/Hero.png"])

    assert not (dest / "CharSet" / "Hero.png").exists()
    assert (dest / "RPG_RT.ldb").exists()
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_staging.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'staging'`）

- [ ] **Step 3: 實作 `staging.py`**

```python
# staging.py
"""把遊戲資料夾 staging 進輸出夾：套排除規則、注入 SF2、選灌 RTP。"""
from __future__ import annotations

import fnmatch
import shutil
from pathlib import Path

DEFAULT_IGNORE = ("*.bak", "*.trans", "index.json", "Thumbs.db", ".DS_Store", "gencache*")
SOUNDFONT_NAME = "easyrpg.soundfont"


def _ignored(rel_posix: str, name: str, ignore_globs, exclude_set) -> bool:
    if rel_posix in exclude_set:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in ignore_globs)


def _copy_tree(src: Path, dest: Path, ignore_globs, exclude_set):
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        rel_posix = rel.as_posix()
        if _ignored(rel_posix, item.name, ignore_globs, exclude_set):
            continue
        # 若任何上層被排除則跳過
        if any(part_posix in exclude_set for part_posix in _ancestors(rel)):
            continue
        target = dest / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _ancestors(rel: Path):
    parts = rel.parts
    for i in range(1, len(parts)):
        yield Path(*parts[:i]).as_posix()


def stage_game(game_dir, dest, *, ignore_globs=DEFAULT_IGNORE,
               exclude_paths=(), soundfont=None, rtp=None) -> None:
    game_dir = Path(game_dir)
    dest = Path(dest)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    exclude_set = {Path(p).as_posix() for p in exclude_paths}

    if rtp:
        _copy_tree(Path(rtp), dest, ignore_globs, exclude_set)   # 先鋪 RTP
    _copy_tree(game_dir, dest, ignore_globs, exclude_set)        # 遊戲覆蓋 RTP

    if soundfont:
        shutil.copy2(Path(soundfont), dest / SOUNDFONT_NAME)
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_staging.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: Commit**

```bash
git add staging.py tests/test_staging.py
git commit -m "feat: 遊戲 staging（排除規則、注入 SF2、灌 RTP）"
```

---

### Task 5: `pwa.py` —— manifest 與圖示

**Files:**
- Create: `pwa.py`
- Test: `tests/test_pwa_manifest.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_pwa_manifest.py
import json
from pathlib import Path

import pwa


def test_install_icon_copies_and_returns_rel(tmp_path):
    icon = tmp_path / "src.png"
    icon.write_bytes(b"\x89PNG")
    dist = tmp_path / "dist"
    dist.mkdir()

    rel = pwa.install_icon(dist, icon)

    assert rel == "icons/icon.png"
    assert (dist / "icons" / "icon.png").read_bytes() == b"\x89PNG"


def test_write_manifest_contents(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()

    out = pwa.write_manifest(dist, "花嫁之冠", "icons/icon.png")

    assert out == dist / "manifest.webmanifest"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["name"] == "花嫁之冠"
    assert data["display"] == "standalone"
    assert data["start_url"] == "."
    assert any(i["src"] == "icons/icon.png" for i in data["icons"])
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_manifest.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'pwa'`）

- [ ] **Step 3: 實作 `pwa.py`（先做 install_icon 與 write_manifest）**

```python
# pwa.py
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
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_manifest.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add pwa.py tests/test_pwa_manifest.py
git commit -m "feat: PWA manifest 與圖示安裝"
```

---

### Task 6: `pwa.py` —— service worker（全資產 precache，離線可玩）

**Files:**
- Modify: `pwa.py`
- Test: `tests/test_pwa_sw.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_pwa_sw.py
import re
from pathlib import Path

import pwa


def test_service_worker_precaches_all_dist_files(tmp_path):
    dist = tmp_path / "dist"
    (dist / "games" / "default").mkdir(parents=True)
    (dist / "index.wasm").write_bytes(b"\0asm")
    (dist / "games" / "default" / "RPG_RT.ldb").write_text("x")

    out = pwa.write_service_worker(dist)

    assert out == dist / "service-worker.js"
    text = out.read_text(encoding="utf-8")
    assert "index.wasm" in text
    assert "games/default/RPG_RT.ldb" in text
    # service-worker.js 自己不該被列進 precache（避免自我快取怪象）
    assert "service-worker.js" not in re.search(r"PRECACHE\s*=\s*\[(.*?)\]", text, re.S).group(1)


def test_service_worker_has_install_and_fetch_handlers(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("x")
    text = pwa.write_service_worker(dist).read_text(encoding="utf-8")
    assert "addEventListener('install'" in text
    assert "addEventListener('fetch'" in text
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_sw.py -v`
Expected: FAIL（`AttributeError: module 'pwa' has no attribute 'write_service_worker'`）

- [ ] **Step 3: 在 `pwa.py` 末尾加入 `write_service_worker`**

```python
# 追加到 pwa.py
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
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_sw.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add pwa.py tests/test_pwa_sw.py
git commit -m "feat: service worker 全資產 precache（離線可玩）"
```

---

### Task 7: `pwa.py` —— 改寫 player 的 `index.html`

注入 manifest 連結、apple-touch-icon、iOS PWA meta、viewport、theme-color，以及 service worker 註冊。`<head>` 找不到就退而求其次插在 `</body>` 前。

**Files:**
- Modify: `pwa.py`
- Test: `tests/test_pwa_html.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_pwa_html.py
from pathlib import Path

import pwa


def test_patch_index_html_injects_pwa_tags(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text(
        "<html><head><title>EasyRPG</title></head><body>x</body></html>",
        encoding="utf-8",
    )

    pwa.patch_index_html(dist, "花嫁之冠", "icons/icon.png")

    html = (dist / "index.html").read_text(encoding="utf-8")
    assert 'rel="manifest"' in html
    assert 'manifest.webmanifest' in html
    assert 'apple-touch-icon' in html
    assert 'apple-mobile-web-app-capable' in html
    assert 'serviceWorker' in html  # 註冊腳本
    assert html.count("</head>") == 1  # 沒破壞結構


def test_patch_index_html_without_head_uses_body(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html><body>x</body></html>", encoding="utf-8")

    pwa.patch_index_html(dist, "App", "icons/icon.png")

    html = (dist / "index.html").read_text(encoding="utf-8")
    assert 'rel="manifest"' in html
    assert 'serviceWorker' in html
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_html.py -v`
Expected: FAIL（`AttributeError: module 'pwa' has no attribute 'patch_index_html'`）

- [ ] **Step 3: 在 `pwa.py` 末尾加入 `patch_index_html`**

```python
# 追加到 pwa.py
import html as _html


def _pwa_head(app_label: str, icon_rel: str) -> str:
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
    snippet = _pwa_head(app_label, icon_rel)
    if "</head>" in html:
        html = html.replace("</head>", snippet + "</head>", 1)
    elif "</body>" in html:
        html = html.replace("</body>", snippet + "</body>", 1)
    else:
        html = html + snippet
    index.write_text(html, encoding="utf-8")
    return index
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_html.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add pwa.py tests/test_pwa_html.py
git commit -m "feat: 改寫 index.html 注入 PWA 標籤與 SW 註冊"
```

---

### Task 8: `easyrpg_web_build.py` —— CLI 核心 orchestrator

串起：ensure_player → 複製 player 檔到 dist → stage_game 到 dist/games/default → gencache → PWA（icon/manifest/sw/html）→（選）deploy。

**Files:**
- Create: `easyrpg_web_build.py`
- Test: `tests/test_build_e2e.py`

- [ ] **Step 1: 寫失敗測試（用假 player tarball 做端對端，不連網）**

```python
# tests/test_build_e2e.py
import io
import json
import tarfile
from pathlib import Path

import easyrpg_web_build as core


def _fake_player_tarball(path: Path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in [
            ("index.html", b"<html><head></head><body></body></html>"),
            ("index.js", b"// js"),
            ("index.wasm", b"\0asm"),
        ]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    path.write_bytes(buf.getvalue())


def _make_game(root: Path):
    root.mkdir()
    (root / "RPG_RT.ldb").write_text("x")
    (root / "RPG_RT.lmt").write_text("x")
    cs = root / "CharSet"
    cs.mkdir()
    (cs / "Hero.png").write_bytes(b"png")


def test_build_produces_self_contained_dist(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    game = tmp_path / "MyGame"
    _make_game(game)
    sf = tmp_path / "win.sf2"
    sf.write_bytes(b"RIFFsfbk")
    icon = tmp_path / "icon.png"
    icon.write_bytes(b"\x89PNG")
    out = tmp_path / "dist"

    result = core.build(
        game=game, app_label="花嫁之冠", soundfont=sf, app_icon=icon,
        out=out, player_cache=tmp_path / "cache",
        player_url=tarball.resolve().as_uri(),
    )

    assert result == out
    # player 檔
    assert (out / "index.wasm").exists()
    # 遊戲在 games/default
    assert (out / "games" / "default" / "RPG_RT.ldb").exists()
    assert (out / "games" / "default" / "easyrpg.soundfont").exists()
    # index.json 由 gencache 產出且結構正確
    idx = json.loads((out / "games" / "default" / "index.json").read_text(encoding="utf-8"))
    assert idx["metadata"]["version"] == 2
    assert idx["cache"]["rpg_rt.ldb"] == "RPG_RT.ldb"
    # PWA 外殼
    assert (out / "manifest.webmanifest").exists()
    assert (out / "service-worker.js").exists()
    assert (out / "icons" / "icon.png").exists()
    assert 'rel="manifest"' in (out / "index.html").read_text(encoding="utf-8")


def test_app_label_defaults_to_game_folder_name(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    game = tmp_path / "勇者傳說"
    _make_game(game)
    out = tmp_path / "dist"

    core.build(
        game=game, soundfont=None, app_icon=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )

    manifest = json.loads((out / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["name"] == "勇者傳說"


def test_build_rejects_non_rpgmaker_folder(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    game = tmp_path / "NotAGame"
    game.mkdir()
    (game / "readme.txt").write_text("nope")
    out = tmp_path / "dist"

    try:
        core.build(
            game=game, out=out, player_cache=tmp_path / "cache",
            player_url=tarball.resolve().as_uri(),
        )
        assert False, "應該因缺 RPG_RT.* 而報錯"
    except core.BuildError:
        pass
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_build_e2e.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'easyrpg_web_build'`）

- [ ] **Step 3: 實作 `easyrpg_web_build.py`**

```python
# easyrpg_web_build.py
"""CLI 核心：把 RPG Maker 遊戲打包成 EasyRPG 網頁版/PWA（dist/）。"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import gencache
import player_fetch
import pwa
import staging

HERE = Path(__file__).resolve().parent
DEFAULT_SOUNDFONT = HERE / "assets" / "easyrpg.soundfont"
DEFAULT_ICON = HERE / "assets" / "app_icon.png"
PLAYER_FILES = ("index.html", "index.js", "index.wasm")


class BuildError(Exception):
    pass


def _log(msg, cb=None):
    if cb:
        cb(msg)
    else:
        print(msg)


def _validate_game(game: Path):
    if not game.is_dir():
        raise BuildError(f"遊戲資料夾不存在：{game}")
    has_db = any((game / n).exists() for n in ("RPG_RT.ldb", "RPG_RT.lmt"))
    if not has_db:
        raise BuildError(f"這不像 RPG Maker 2000/2003 遊戲（缺 RPG_RT.ldb/.lmt）：{game}")


def _read_exclude_file(path) -> list:
    if not path:
        return []
    return [ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")]


def build(*, game, app_label=None, soundfont=DEFAULT_SOUNDFONT, app_icon=DEFAULT_ICON,
          rtp=None, out="dist", ignore=None, exclude_file=None,
          refresh_player=False, deploy=False, player_cache=".player-cache",
          player_url=player_fetch.PLAYER_URL, log=None) -> Path:
    game = Path(game)
    out = Path(out)
    _validate_game(game)
    app_label = app_label or game.name

    _log("下載/取用 web player…", log)
    player_dir = player_fetch.ensure_player(player_cache, url=player_url, refresh=refresh_player)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in PLAYER_FILES:
        shutil.copy2(player_dir / name, out / name)

    _log("整理遊戲資料…", log)
    game_dest = out / "games" / "default"
    ignore_globs = tuple(ignore) if ignore else staging.DEFAULT_IGNORE
    staging.stage_game(
        game, game_dest, ignore_globs=ignore_globs,
        exclude_paths=_read_exclude_file(exclude_file),
        soundfont=soundfont, rtp=rtp,
    )

    _log("產生 index.json（gencache）…", log)
    gencache.write_index(game_dest)

    _log("鋪 PWA 外殼…", log)
    icon_rel = pwa.install_icon(out, app_icon) if app_icon else pwa.ICON_REL
    pwa.write_manifest(out, app_label, icon_rel)
    pwa.patch_index_html(out, app_label, icon_rel)
    pwa.write_service_worker(out)  # 最後做，才能 precache 全部資產

    if deploy:
        import deploy as deploy_mod
        _log("部署到 GitHub Pages…", log)
        deploy_mod.deploy_gh_pages(out, log=log)

    _log(f"完成：{out}", log)
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description="把 RPG Maker 遊戲打包成 EasyRPG 網頁版/PWA")
    p.add_argument("--game", required=True, help="遊戲資料夾（含 RPG_RT.ldb/.lmt）")
    p.add_argument("--app-label", default=None, help="App 顯示名稱（預設＝資料夾名）")
    p.add_argument("--soundfont", default=str(DEFAULT_SOUNDFONT))
    p.add_argument("--app-icon", default=str(DEFAULT_ICON))
    p.add_argument("--rtp", default=None)
    p.add_argument("--out", default="dist")
    p.add_argument("--ignore", action="append", default=None, help="忽略 glob（可重複）")
    p.add_argument("--exclude-file", default=None)
    p.add_argument("--refresh-player", action="store_true")
    p.add_argument("--deploy", action="store_true")
    args = p.parse_args(argv)
    try:
        build(
            game=args.game, app_label=args.app_label, soundfont=args.soundfont,
            app_icon=args.app_icon, rtp=args.rtp, out=args.out, ignore=args.ignore,
            exclude_file=args.exclude_file, refresh_player=args.refresh_player,
            deploy=args.deploy,
        )
    except BuildError as e:
        print("錯誤：", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_build_e2e.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 跑全部測試**

Run: `python -m pytest -v`
Expected: 全部 PASS

- [ ] **Step 6: Commit**

```bash
git add easyrpg_web_build.py tests/test_build_e2e.py
git commit -m "feat: CLI 核心 orchestrator（player→staging→gencache→PWA）"
```

---

### Task 9: `deploy.py` —— 一鍵 push 到 `gh-pages`

用暫時 git worktree 把 `dist/` 內容變成 `gh-pages` 分支的提交並 push。需專案已設定 GitHub remote。測試用 `dry_run` 只回傳將執行的指令，不真的跑 git。

**Files:**
- Create: `deploy.py`
- Test: `tests/test_deploy.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_deploy.py
from pathlib import Path

import deploy


def test_deploy_dry_run_returns_git_plan(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("x")

    cmds = deploy.deploy_gh_pages(dist, branch="gh-pages", dry_run=True)

    joined = "\n".join(" ".join(c) for c in cmds)
    assert "gh-pages" in joined
    assert any("push" in c for c in cmds)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_deploy.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'deploy'`）

- [ ] **Step 3: 實作 `deploy.py`**

```python
# deploy.py
"""把 dist/ 內容 push 到 gh-pages 分支（GitHub Pages）。"""
from __future__ import annotations

import subprocess
from pathlib import Path


def _plan(dist: Path, remote: str, branch: str) -> list:
    # 用 git 的 --work-tree 把 dist 當工作樹，提交到孤立分支再 push。
    return [
        ["git", "switch", "--orphan", branch],
        ["git", "--work-tree", str(dist), "add", "-A"],
        ["git", "--work-tree", str(dist), "commit", "-m", "deploy: 更新 GitHub Pages"],
        ["git", "push", "-f", remote, branch],
    ]


def deploy_gh_pages(dist, remote: str = "origin", branch: str = "gh-pages",
                    dry_run: bool = False, log=None) -> list:
    dist = Path(dist)
    cmds = _plan(dist, remote, branch)
    if dry_run:
        return cmds
    for cmd in cmds:
        if log:
            log("$ " + " ".join(cmd))
        subprocess.run(cmd, check=True)
    return cmds
```

> 注意：實作者執行真部署前，需先 `git remote add origin <GitHub repo>`。`deploy_gh_pages` 的非 dry-run 路徑會切到孤立分支，請在乾淨工作樹上執行（已 commit 程式碼後）。本任務只驗證 dry-run 計畫；真部署在 Task 12 手動驗證。

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_deploy.py -v`
Expected: PASS（1 passed）

- [ ] **Step 5: Commit**

```bash
git add deploy.py tests/test_deploy.py
git commit -m "feat: --deploy 一鍵 push 到 gh-pages"
```

---

### Task 10: `easyrpg_web_gui.py` —— Tkinter GUI（薄前端）

鏡射既有 `C:\opensource\easyRPG\easyrpg_gui.py` 結構：ttk 表單 + ScrolledText log + threading/queue 非阻塞，`import easyrpg_web_build as core`，按鈕呼叫 `core.build(..., log=回呼)`。

**Files:**
- Create: `easyrpg_web_gui.py`
- Test: `tests/test_gui_smoke.py`

- [ ] **Step 1: 寫失敗測試（只驗證可匯入且為薄前端，不開真視窗）**

```python
# tests/test_gui_smoke.py
import importlib

import easyrpg_web_build as core


def test_gui_imports_and_references_core():
    mod = importlib.import_module("easyrpg_web_gui")
    # GUI 必須透過核心，不得自行重寫打包邏輯
    assert mod.core is core
    assert hasattr(mod, "App")
    assert callable(core.build)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_gui_smoke.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'easyrpg_web_gui'`）

- [ ] **Step 3: 實作 `easyrpg_web_gui.py`**

```python
# easyrpg_web_gui.py
"""easyRPG-web 的 Tkinter GUI（薄前端，呼叫 easyrpg_web_build 核心）。"""
from __future__ import annotations

import queue
import threading
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import easyrpg_web_build as core


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("EasyRPG → 網頁版/PWA 打包工具")
        self.log_q: queue.Queue = queue.Queue()

        self.game = tk.StringVar()
        self.label = tk.StringVar()
        self.soundfont = tk.StringVar(value=str(core.DEFAULT_SOUNDFONT))
        self.icon = tk.StringVar(value=str(core.DEFAULT_ICON))
        self.rtp = tk.StringVar()
        self.out = tk.StringVar(value="dist")
        self.deploy = tk.BooleanVar(value=False)
        self.refresh = tk.BooleanVar(value=False)

        self._build_form()
        self.root.after(100, self._drain_log)

    def _row(self, parent, r, text, var, picker):
        ttk.Label(parent, text=text).grid(row=r, column=0, sticky="w", padx=4, pady=3)
        ttk.Entry(parent, textvariable=var, width=48).grid(row=r, column=1, padx=4)
        if picker:
            ttk.Button(parent, text="…", width=3, command=picker).grid(row=r, column=2)

    def _build_form(self):
        f = ttk.Frame(self.root, padding=10)
        f.grid(sticky="nsew")
        self._row(f, 0, "遊戲資料夾", self.game,
                  lambda: self._pick_dir(self.game, on_game=True))
        self._row(f, 1, "App 名稱", self.label, None)
        self._row(f, 2, "音色 SF2", self.soundfont, lambda: self._pick_file(self.soundfont))
        self._row(f, 3, "App 圖示", self.icon, lambda: self._pick_file(self.icon))
        self._row(f, 4, "RTP（選填）", self.rtp, lambda: self._pick_dir(self.rtp))
        self._row(f, 5, "輸出夾", self.out, lambda: self._pick_dir(self.out))
        ttk.Checkbutton(f, text="完成後部署到 GitHub Pages",
                        variable=self.deploy).grid(row=6, column=1, sticky="w")
        ttk.Checkbutton(f, text="強制更新 web player",
                        variable=self.refresh).grid(row=7, column=1, sticky="w")
        self.run_btn = ttk.Button(f, text="開始打包", command=self._run)
        self.run_btn.grid(row=8, column=1, sticky="w", pady=6)
        self.log = ScrolledText(f, width=70, height=16, state="disabled")
        self.log.grid(row=9, column=0, columnspan=3, pady=6)

    def _pick_dir(self, var, on_game=False):
        d = filedialog.askdirectory()
        if d:
            var.set(d)
            if on_game and not self.label.get():
                self.label.set(Path(d).name)

    def _pick_file(self, var):
        p = filedialog.askopenfilename()
        if p:
            var.set(p)

    def _emit(self, msg):
        self.log_q.put(msg)

    def _drain_log(self):
        while not self.log_q.empty():
            msg = self.log_q.get()
            self.log.configure(state="normal")
            self.log.insert("end", msg + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.root.after(100, self._drain_log)

    def _run(self):
        if not self.game.get():
            messagebox.showerror("缺少設定", "請先選遊戲資料夾")
            return
        self.run_btn.configure(state="disabled")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            out = core.build(
                game=self.game.get(),
                app_label=self.label.get() or None,
                soundfont=self.soundfont.get() or None,
                app_icon=self.icon.get() or None,
                rtp=self.rtp.get() or None,
                out=self.out.get() or "dist",
                refresh_player=self.refresh.get(),
                deploy=self.deploy.get(),
                log=self._emit,
            )
            self._emit(f"✓ 完成，輸出在：{out}")
        except Exception as e:  # noqa: BLE001 — GUI 需把任何錯誤回報給使用者
            self._emit(f"✗ 失敗：{e}")
        finally:
            self.root.after(0, lambda: self.run_btn.configure(state="normal"))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_gui_smoke.py -v`
Expected: PASS（1 passed）

- [ ] **Step 5: 手動開一次 GUI 確認版面（可選但建議）**

Run: `python easyrpg_web_gui.py`
Expected: 視窗開啟，欄位齊全，關閉視窗即可。

- [ ] **Step 6: Commit**

```bash
git add easyrpg_web_gui.py tests/test_gui_smoke.py
git commit -m "feat: Tkinter GUI（薄前端，呼叫 build 核心）"
```

---

### Task 11: 啟動器與 README

**Files:**
- Create: `啟動GUI.bat`（UTF-8 **BOM**）
- Create: `啟動.bat`（UTF-8 **BOM**）
- Create: `run.sh`（LF、no-BOM）
- Create: `README.md`

> 編碼規則（沿用既有專案）：含中文的 `.bat` 必須存成 **UTF-8 with BOM**，否則 Windows 主控台會亂碼/解析錯誤；`.sh` 存 **LF、no-BOM**。

- [ ] **Step 1: 建 `啟動GUI.bat`（UTF-8 BOM）**

```bat
@echo off
chcp 65001 >nul
python "%~dp0easyrpg_web_gui.py"
pause
```

- [ ] **Step 2: 建 `啟動.bat`（UTF-8 BOM，CLI 進階用）**

```bat
@echo off
chcp 65001 >nul
python "%~dp0easyrpg_web_build.py" %*
pause
```

- [ ] **Step 3: 建 `run.sh`（LF、no-BOM）**

```sh
#!/usr/bin/env bash
cd "$(dirname "$0")" && python3 easyrpg_web_gui.py
```

- [ ] **Step 4: 建 `README.md`**

````markdown
# EasyRPG → iOS 網頁版 / PWA 打包工具

把 RPG Maker 2000/2003 遊戲打包成**自包含的網頁 App**，部署到 GitHub Pages 後，
iPhone 用 Safari 開、按「加入主畫面」即得**全螢幕、有圖示、可離線**的 App，MIDI 音色比照 Windows。
**純 Windows 可用，不需 Mac、不需編譯。**

## 為什麼是網頁版而不是 .ipa？
原生 iOS `.ipa` 一定要 macOS + Xcode 編譯與簽章（Apple 鎖死），Windows 做不到。
網頁/PWA 是純 Windows 能完成、又能在 iPhone 上像 App 一樣全螢幕離線遊玩的方案。

## 前置需求
- Python 3.8+（僅標準庫）。
- 一個 GitHub repo（要用 GitHub Pages 上線時）。

## GUI（推薦）
- Windows：雙擊 `啟動GUI.bat`
- macOS/Linux：`./run.sh`

選遊戲資料夾 → （可改名稱/音色/圖示）→「開始打包」→ 產物在 `dist/`。

## CLI
```bash
python easyrpg_web_build.py --game "C:/Games/花嫁之冠" --app-label 花嫁之冠
```
| 參數 | 說明 |
|---|---|
| `--game`（必） | 遊戲資料夾（含 `RPG_RT.ldb`/`.lmt`） |
| `--app-label` | App 名稱（預設＝資料夾名） |
| `--soundfont` | SF2 音色（預設內附 Windows 音色） |
| `--app-icon` | App 圖示 PNG（預設內附） |
| `--rtp` | RTP 資料夾，先灌入再打包 |
| `--ignore` | 忽略 glob（可重複；預設排除 `*.bak`/`*.trans` 等） |
| `--exclude-file` | 排除清單檔（每行一個相對路徑） |
| `--out` | 輸出夾（預設 `dist`） |
| `--refresh-player` | 強制重抓官方 web player |
| `--deploy` | 完成後 push 到 `gh-pages` |

## 本機測試
```bash
cd dist && python -m http.server
```
電腦瀏覽器開 `http://localhost:8000` 應自動啟動遊戲。
手機同 Wi-Fi 可開 `http://<電腦區網IP>:8000`（注意：純 http 非 localhost 時 service worker 不啟用，離線功能要上 HTTPS 才生效）。

## 上線到 GitHub Pages（iPhone 安裝）
1. `--deploy`（或手動把 `dist/` 內容 push 到 `gh-pages` 分支）。
2. repo 設定啟用 Pages（來源選 `gh-pages`）。
3. iPhone Safari 開該 HTTPS 網址 → 分享 →「加入主畫面」→ 全螢幕 App。

## 注意
- 音色 SF2 別過大（內附 Windows 音色約 3 MB，OK）。
- 遊戲依賴 RTP 時請用 `--rtp` 一併打包。
````

- [ ] **Step 5: 確認 `.bat` 是 UTF-8 BOM**

Run（PowerShell）：`Format-Hex 啟動GUI.bat | Select-Object -First 1`
Expected: 開頭為 `EF BB BF`（BOM）。若否，用編輯器另存為 UTF-8 with BOM。

- [ ] **Step 6: Commit**

```bash
git add 啟動GUI.bat 啟動.bat run.sh README.md
git commit -m "docs: 啟動器與 README"
```

---

### Task 12: 端對端真實驗證（真 player + 真遊戲）

用真實下載的 player 與既有遊戲跑一次，確認在瀏覽器能起動。

**Files:** 無（驗證用）

- [ ] **Step 1: 跑全部單元測試**

Run: `python -m pytest -v`
Expected: 全部 PASS。

- [ ] **Step 2: 用既有遊戲真打包（會真的連網抓 player）**

Run: `python easyrpg_web_build.py --game "C:/opensource/easyRPG/game" --app-label TestGame`
Expected: 印出各階段並以 `完成：dist` 結束；`dist/index.wasm`、`dist/games/default/index.json`、`dist/manifest.webmanifest`、`dist/service-worker.js` 皆存在。

- [ ] **Step 3: 本機起伺服器**

Run: `cd dist && python -m http.server 8000`（背景執行）

- [ ] **Step 4: 瀏覽器驗證**

開 `http://localhost:8000` → 確認遊戲**自動啟動**（無選單）、畫面/BGM 正常。記錄結果。

- [ ] **Step 5: 收尾**

```bash
git add -A
git commit -m "chore: 端對端驗證通過（dist 可在瀏覽器啟動）" --allow-empty
```

---

## 自我審查結果（對照 spec）

- **Spec 覆蓋：** 不編譯/用官方 player（Task 3）、staging+排除+SF2+RTP（Task 4）、純 Python gencache 與正確 index.json schema（Task 2）、PWA manifest/離線 SW/圖示/index.html 改寫（Task 5–7）、CLI 介面與全參數（Task 8）、GitHub Pages 部署（Task 9）、Tkinter GUI 薄前端（Task 10）、啟動器/README/編碼規則（Task 11）、端對端驗證（Task 12）。✔ 全部對應。
- **Placeholder 掃描：** 無 TBD/TODO；每段含完整可執行碼與預期輸出。✔
- **型別/簽章一致性：** `generate_index`/`write_index`、`ensure_player(cache, url=, refresh=)`、`stage_game(..., ignore_globs=, exclude_paths=, soundfont=, rtp=)`、`pwa.install_icon/write_manifest/write_service_worker/patch_index_html`、`core.build(..., player_url=, log=)`、`deploy_gh_pages(dist, remote=, branch=, dry_run=, log=)` 在各 task 間一致。✔
- **已知風險：** 真 player 的 `index.html` 結構未知 → Task 7 用「找 `</head>` 否則 `</body>`」的健壯插入；真實啟動由 Task 12 驗證。gencache schema 已對照官方 C++ 原始碼。✔
