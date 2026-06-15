# 多遊戲庫 + 圖示網格選單 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 easyRPG-web 從「單一遊戲」擴充成「多遊戲庫」：一次打包多個 RPG Maker 遊戲成單一 PWA，開啟即見圖示網格選單，點任一遊戲進去玩，全程可用 GUI 完成。

**Architecture:** 新增 `slugify.py`（唯一安全 slug）、`menu.py`（產生圖示網格 `index.html`）、`library.py`（多遊戲各自 staging + gencache + 封面）。`easyrpg_web_build.py` 新增 `build_library()`：取回官方 player 後把其 `index.html` patch 並改名為 `play.html`，各遊戲進 `games/<slug>/`，再由 `menu.py` 產生網格 `index.html`，最後鋪 PWA 外殼（manifest/SW）。`easyrpg_web_gui.py` 改寫成 `ttk.Treeview` 清單編輯器，呼叫 `build_library`。重用既有 `staging`/`gencache`/`player_fetch`/`pwa`，單一遊戲 `build()` 保留。

**Tech Stack:** Python 3.8+（僅標準庫：`unicodedata`/`re`/`urllib.parse`/`html`/`shutil`/`pathlib`/`tkinter`）；pytest。

**Spec:** `docs/superpowers/specs/2026-06-15-multi-game-library-design.md`
**專案根目錄：** `C:\opensource\easyRPG-web\`（分支 `feat/multi-game-library`）

---

## 檔案結構

| 檔案 | 變更 | 職責 |
|---|---|---|
| `slugify.py` | 新增 | 名稱 → 唯一、檔名/網址安全的 slug |
| `menu.py` | 新增 | 產生圖示網格「遊戲庫選單」`index.html`（重用 `pwa._pwa_head`） |
| `library.py` | 新增 | 多遊戲各自 staging 到 `games/<slug>/`、gencache、複製封面；回傳選單用 entries |
| `easyrpg_web_build.py` | 修改 | `_validate_game` 加 `label` 參數；新增 `build_library()`；`import library, menu, slugify` |
| `easyrpg_web_gui.py` | 重寫 | Treeview 清單編輯器，呼叫 `build_library` |
| `tests/test_slugify.py` … | 新增/改 | 各模組 TDD 測試 |

---

### Task 1: `slugify.py` —— 唯一安全 slug

**Files:**
- Create: `slugify.py`
- Test: `tests/test_slugify.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_slugify.py
import slugify


def test_basic_lowercase_and_spaces():
    assert slugify.slugify("Hero Quest") == "hero-quest"


def test_removes_unsafe_chars():
    assert slugify.slugify('a/b:c*?"<>|d') == "abcd"


def test_keeps_cjk():
    assert slugify.slugify("花嫁之冠") == "花嫁之冠"


def test_empty_falls_back():
    assert slugify.slugify("   ") == "game"
    assert slugify.slugify("/:*") == "game"


def test_uniqueness_with_taken_set():
    taken = set()
    assert slugify.slugify("Hero", taken) == "hero"
    assert slugify.slugify("Hero", taken) == "hero-2"
    assert slugify.slugify("Hero", taken) == "hero-3"
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_slugify.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'slugify'`）

- [ ] **Step 3: 實作 `slugify.py`**

```python
# slugify.py
"""把名稱轉成唯一、檔名與網址安全的 slug（保留 CJK）。"""
from __future__ import annotations

import re
import unicodedata

_UNSAFE = re.compile(r'[\\/:*?"<>|]')
_SPACES = re.compile(r"\s+")
_DASHES = re.compile(r"-+")


def _base_slug(name: str) -> str:
    s = unicodedata.normalize("NFKC", str(name)).strip().lower()
    s = _UNSAFE.sub("", s)
    s = _SPACES.sub("-", s)
    s = _DASHES.sub("-", s).strip("-")
    return s or "game"


def slugify(name: str, taken=None) -> str:
    """回傳唯一 slug；若提供 taken 集合，會避開其中已用過的並把結果加入。"""
    base = _base_slug(name)
    slug = base
    i = 2
    if taken is not None:
        while slug in taken:
            slug = f"{base}-{i}"
            i += 1
        taken.add(slug)
    return slug
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_slugify.py -v`
Expected: PASS（5 passed）

- [ ] **Step 5: Commit**

```bash
git add slugify.py tests/test_slugify.py
git commit -m "feat: slugify（唯一安全 slug，保留 CJK）"
```

---

### Task 2: `menu.py` —— 圖示網格選單

**Files:**
- Create: `menu.py`
- Test: `tests/test_menu.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_menu.py
from pathlib import Path

import menu


def test_write_menu_generates_grid(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    entries = [
        {"label": "花嫁之冠", "slug": "花嫁之冠", "cover_rel": "games/花嫁之冠/cover.png"},
        {"label": "A & B", "slug": "a-b", "cover_rel": None},
    ]

    out = menu.write_menu(dist, "我的遊戲庫", entries)

    assert out == dist / "index.html"
    html = out.read_text(encoding="utf-8")
    # 標題
    assert "我的遊戲庫" in html
    # 第一個遊戲：slug 經 URL 編碼放進 href
    assert "play.html?game=%E8%8A%B1%E5%AB%81%E4%B9%8B%E5%86%A0" in html
    assert "games/花嫁之冠/cover.png" in html
    # 第二個遊戲：無封面 → 用預設圖示；label 經 HTML 跳脫
    assert "icons/icon.png" in html
    assert "A &amp; B" in html
    # PWA 標籤（選單頁就是 start_url，要可安裝 + 註冊 SW）
    assert 'rel="manifest"' in html
    assert "serviceWorker" in html


def test_write_menu_one_card_per_entry(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    entries = [
        {"label": "G1", "slug": "g1", "cover_rel": None},
        {"label": "G2", "slug": "g2", "cover_rel": None},
        {"label": "G3", "slug": "g3", "cover_rel": None},
    ]
    out = menu.write_menu(dist, "Lib", entries)
    html = out.read_text(encoding="utf-8")
    assert html.count('class="card"') == 3
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_menu.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'menu'`）

- [ ] **Step 3: 實作 `menu.py`**（用 `.replace` 避開 CSS 的大括號與 `str.format` 衝突；重用 `pwa._pwa_head` 注入 PWA 標籤）

```python
# menu.py
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
        _PAGE.replace("__PWAHEAD__", pwa._pwa_head(app_label, icon_rel))
        .replace("__TITLE__", _html.escape(app_label))
        .replace("__CARDS__", "\n".join(cards))
    )
    out = Path(dist) / "index.html"
    out.write_text(page, encoding="utf-8")
    return out
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_menu.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add menu.py tests/test_menu.py
git commit -m "feat: 圖示網格遊戲庫選單頁"
```

---

### Task 3: `library.py` —— 多遊戲 staging

**Files:**
- Create: `library.py`
- Test: `tests/test_library.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_library.py
from pathlib import Path

import library


def _game(root: Path, marker: str):
    root.mkdir()
    (root / "RPG_RT.ldb").write_text(marker)


def test_stage_library_two_games(tmp_path):
    out = tmp_path / "dist"
    g1 = tmp_path / "g1"
    _game(g1, "one")
    g2 = tmp_path / "g2"
    _game(g2, "two")
    cover = tmp_path / "c.png"
    cover.write_bytes(b"\x89PNG")
    sf = tmp_path / "sf.sf2"
    sf.write_bytes(b"SF2")
    games = [
        {"folder": g1, "label": "Game One", "slug": "game-one", "cover": cover},
        {"folder": g2, "label": "Game Two", "slug": "game-two", "cover": None},
    ]

    entries = library.stage_library(out, games, soundfont=sf)

    # 各遊戲進自己的 slug 夾，含 index.json 與共用音色
    assert (out / "games" / "game-one" / "index.json").exists()
    assert (out / "games" / "game-one" / "easyrpg.soundfont").exists()
    assert (out / "games" / "game-two" / "index.json").exists()
    # 有封面的複製成 cover.png；沒封面的不產
    assert (out / "games" / "game-one" / "cover.png").read_bytes() == b"\x89PNG"
    assert not (out / "games" / "game-two" / "cover.png").exists()
    # 回傳的 entries 供選單使用
    assert entries[0] == {"label": "Game One", "slug": "game-one",
                          "cover_rel": "games/game-one/cover.png"}
    assert entries[1] == {"label": "Game Two", "slug": "game-two", "cover_rel": None}


def test_stage_library_cover_not_in_index_json(tmp_path):
    out = tmp_path / "dist"
    g1 = tmp_path / "g1"
    _game(g1, "one")
    cover = tmp_path / "c.png"
    cover.write_bytes(b"\x89PNG")
    games = [{"folder": g1, "label": "G", "slug": "g", "cover": cover}]

    library.stage_library(out, games, soundfont=None)

    import json
    idx = json.loads((out / "games" / "g" / "index.json").read_text(encoding="utf-8"))
    assert "cover" not in idx["cache"]  # 封面在 gencache 之後才複製，不入索引
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_library.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'library'`）

- [ ] **Step 3: 實作 `library.py`**

```python
# library.py
"""把多個遊戲各自 staging 到 dist/games/<slug>/，產 index.json，複製封面。"""
from __future__ import annotations

import shutil
from pathlib import Path

import gencache
import staging


def stage_library(out, games, *, soundfont=None, ignore_globs=staging.DEFAULT_IGNORE):
    """games: list of {folder, label, slug, cover(optional)}。
    回傳選單用 entries: list of {label, slug, cover_rel}。"""
    out = Path(out)
    entries = []
    for g in games:
        slug = g["slug"]
        dest = out / "games" / slug
        staging.stage_game(g["folder"], dest, ignore_globs=ignore_globs, soundfont=soundfont)
        gencache.write_index(dest)  # 在複製封面前產索引，封面就不會進 index.json
        cover_rel = None
        if g.get("cover"):
            shutil.copy2(Path(g["cover"]), dest / "cover.png")
            cover_rel = f"games/{slug}/cover.png"
        entries.append({"label": g["label"], "slug": slug, "cover_rel": cover_rel})
    return entries
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_library.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add library.py tests/test_library.py
git commit -m "feat: 多遊戲 staging（各自 gencache + 封面）"
```

---

### Task 4: `easyrpg_web_build.py` —— `build_library()`

**Files:**
- Modify: `easyrpg_web_build.py`
- Test: `tests/test_build_library.py`

- [ ] **Step 1: 寫失敗測試**

```python
# tests/test_build_library.py
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


def _game(root: Path, marker: str):
    root.mkdir()
    (root / "RPG_RT.ldb").write_text(marker)


def test_build_library_two_games(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    g1 = tmp_path / "Hanayome"
    _game(g1, "1")
    g2 = tmp_path / "Brave"
    _game(g2, "2")
    out = tmp_path / "dist"

    result = core.build_library(
        games=[{"folder": g1, "label": "花嫁之冠", "cover": None},
               {"folder": g2, "label": "勇者傳說", "cover": None}],
        app_label="我的遊戲庫", app_icon=None, soundfont=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )

    assert result == out
    # player 改名成 play.html，並被 patch 過（含 SW 註冊）
    assert (out / "play.html").exists()
    assert not (out / "index.html").read_text(encoding="utf-8").startswith("<html><head></head>")
    play = (out / "play.html").read_text(encoding="utf-8")
    assert "serviceWorker" in play
    # 網格選單 index.html 連到兩個遊戲
    grid = (out / "index.html").read_text(encoding="utf-8")
    assert "我的遊戲庫" in grid
    assert "play.html?game=" in grid
    assert grid.count('class="card"') == 2
    # 各遊戲資料
    assert (out / "games" / "花嫁之冠" / "index.json").exists()
    assert (out / "games" / "勇者傳說" / "index.json").exists()
    # PWA
    manifest = json.loads((out / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["start_url"] == "."
    sw = (out / "service-worker.js").read_text(encoding="utf-8")
    assert "play.html" in sw
    assert "games/花嫁之冠/index.json" in sw


def test_build_library_empty_rejected(tmp_path):
    try:
        core.build_library(games=[], out=tmp_path / "dist")
        assert False, "空清單應報錯"
    except core.BuildError:
        pass


def test_build_library_names_invalid_game(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    good = tmp_path / "Good"
    _game(good, "1")
    bad = tmp_path / "Bad"
    bad.mkdir()
    (bad / "readme.txt").write_text("nope")
    out = tmp_path / "dist"

    try:
        core.build_library(
            games=[{"folder": good, "label": "好遊戲", "cover": None},
                   {"folder": bad, "label": "壞遊戲", "cover": None}],
            app_icon=None, soundfont=None, out=out,
            player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
        )
        assert False, "非法遊戲應中止"
    except core.BuildError as e:
        assert "壞遊戲" in str(e)  # 指名是哪個


def test_build_library_assigns_unique_slugs(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    g1 = tmp_path / "A"
    _game(g1, "1")
    g2 = tmp_path / "B"
    _game(g2, "2")
    out = tmp_path / "dist"

    core.build_library(
        games=[{"folder": g1, "label": "Dungeon", "cover": None},
               {"folder": g2, "label": "Dungeon", "cover": None}],  # 同名
        app_icon=None, soundfont=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )
    assert (out / "games" / "dungeon" / "index.json").exists()
    assert (out / "games" / "dungeon-2" / "index.json").exists()
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_build_library.py -v`
Expected: FAIL（`AttributeError: module 'easyrpg_web_build' has no attribute 'build_library'`）

- [ ] **Step 3a: 修改 `_validate_game` 加 `label` 參數**

把現有：
```python
def _validate_game(game: Path):
    if not game.is_dir():
        raise BuildError(f"遊戲資料夾不存在：{game}")
    has_db = any((game / n).exists() for n in ("RPG_RT.ldb", "RPG_RT.lmt"))
    if not has_db:
        raise BuildError(f"這不像 RPG Maker 2000/2003 遊戲（缺 RPG_RT.ldb/.lmt）：{game}")
```
改成：
```python
def _validate_game(game: Path, label=None):
    who = f"遊戲「{label}」" if label else "遊戲資料夾"
    if not game.is_dir():
        raise BuildError(f"{who}不存在：{game}")
    has_db = any((game / n).exists() for n in ("RPG_RT.ldb", "RPG_RT.lmt"))
    if not has_db:
        raise BuildError(f"{who}不是合法的 RPG Maker 2000/2003 遊戲（缺 RPG_RT.ldb/.lmt）：{game}")
```

- [ ] **Step 3b: 在 import 區加入新模組**

把現有：
```python
import gencache
import player_fetch
import pwa
import staging
```
改成：
```python
import gencache
import library
import menu
import player_fetch
import pwa
import slugify
import staging
```

- [ ] **Step 3c: 在 `build()` 函式之後新增 `build_library()`**

```python
def build_library(*, games, app_label="我的遊戲庫", app_icon=DEFAULT_ICON,
                  soundfont=DEFAULT_SOUNDFONT, out="dist", ignore=None,
                  refresh_player=False, deploy=False, player_cache=".player-cache",
                  player_url=player_fetch.PLAYER_URL, log=None) -> Path:
    out = Path(out)
    if not games:
        raise BuildError("遊戲庫至少要一個遊戲。")

    specs = [dict(g) for g in games]
    taken = set()
    for g in specs:
        folder = Path(g["folder"])
        label = g.get("label") or folder.name
        _validate_game(folder, label)
        g["folder"] = folder
        g["label"] = label
        g["slug"] = slugify.slugify(label, taken)

    _log("下載/取用 web player…", log)
    player_dir = player_fetch.ensure_player(player_cache, url=player_url, refresh=refresh_player)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name in PLAYER_FILES:
        shutil.copy2(player_dir / name, out / name)

    icon_rel = pwa.install_icon(out, app_icon) if app_icon else pwa.ICON_REL
    pwa.patch_index_html(out, app_label, icon_rel)   # 先 patch player 的 index.html
    (out / "index.html").rename(out / "play.html")    # player → play.html

    _log("整理各遊戲…", log)
    ignore_globs = tuple(ignore) if ignore else staging.DEFAULT_IGNORE
    entries = library.stage_library(out, specs, soundfont=soundfont, ignore_globs=ignore_globs)

    _log("產生遊戲庫選單…", log)
    menu.write_menu(out, app_label, entries, icon_rel)  # 寫新的 index.html（網格）

    pwa.write_manifest(out, app_label, icon_rel)
    pwa.write_service_worker(out)                        # 最後：precache 全部資產

    if deploy:
        import deploy as deploy_mod
        _log("部署到 GitHub Pages…", log)
        deploy_mod.deploy_gh_pages(out, log=log)

    _log(f"完成：{out}", log)
    return out
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_build_library.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: 跑全部測試確認沒弄壞單一遊戲流程**

Run: `python -m pytest -q`
Expected: 全部 PASS（原 22 + 本計畫新增）

- [ ] **Step 6: Commit**

```bash
git add easyrpg_web_build.py tests/test_build_library.py
git commit -m "feat: build_library（多遊戲→play.html+網格選單+PWA）"
```

---

### Task 5: `easyrpg_web_gui.py` —— 改寫成清單編輯器

**Files:**
- Modify（整檔重寫）: `easyrpg_web_gui.py`
- Test: `tests/test_gui_smoke.py`（更新）

- [ ] **Step 1: 更新 smoke 測試**

把 `tests/test_gui_smoke.py` 整檔換成：
```python
import importlib

import easyrpg_web_build as core


def test_gui_imports_and_references_core():
    mod = importlib.import_module("easyrpg_web_gui")
    assert mod.core is core
    assert hasattr(mod, "App")
    # GUI 走遊戲庫核心，且舊單一遊戲核心仍在
    assert callable(core.build_library)
    assert callable(core.build)
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_gui_smoke.py -v`
Expected: FAIL（`AttributeError: module 'easyrpg_web_build' has no attribute 'build_library'` 已在 Task 4 解除；此處若 GUI 尚未改寫，測試仍會因 `core.build_library` 存在而 PASS — 故先確認失敗點：在改寫前，本測試其實會 PASS。若已 PASS 可直接進 Step 3 改寫並保持綠燈。）

> 註：本任務的 smoke 測試是「不退步」保護，不是紅燈驅動。重點是 Step 3 重寫後仍綠。

- [ ] **Step 3: 整檔重寫 `easyrpg_web_gui.py`**

```python
# easyrpg_web_gui.py
"""easyRPG-web 遊戲庫 GUI（Tkinter 清單編輯器，呼叫 build_library 核心）。"""
from __future__ import annotations

import queue
import threading
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import easyrpg_web_build as core


class GameDialog(tk.Toplevel):
    """加入/編輯單一遊戲：名稱 + 封面（選填）。回傳 dict 或 None。"""

    def __init__(self, parent, folder, label="", cover=""):
        super().__init__(parent)
        self.title("遊戲設定")
        self.result = None
        self.transient(parent)
        self.grab_set()

        self.v_label = tk.StringVar(value=label or Path(folder).name)
        self.v_cover = tk.StringVar(value=cover)

        ttk.Label(self, text=f"資料夾：{folder}").grid(row=0, column=0, columnspan=3,
                                                     sticky="w", padx=8, pady=6)
        ttk.Label(self, text="顯示名稱").grid(row=1, column=0, sticky="w", padx=8)
        ttk.Entry(self, textvariable=self.v_label, width=36).grid(row=1, column=1, padx=4)
        ttk.Label(self, text="封面圖（選填）").grid(row=2, column=0, sticky="w", padx=8)
        ttk.Entry(self, textvariable=self.v_cover, width=36).grid(row=2, column=1, padx=4)
        ttk.Button(self, text="…", width=3, command=self._pick_cover).grid(row=2, column=2)
        bar = ttk.Frame(self)
        bar.grid(row=3, column=0, columnspan=3, pady=8)
        ttk.Button(bar, text="確定", command=self._ok).pack(side="left", padx=4)
        ttk.Button(bar, text="取消", command=self.destroy).pack(side="left", padx=4)

        self._folder = folder

    def _pick_cover(self):
        p = filedialog.askopenfilename(
            filetypes=[("圖片", "*.png *.jpg *.jpeg *.gif"), ("全部", "*.*")])
        if p:
            self.v_cover.set(p)

    def _ok(self):
        if not self.v_label.get().strip():
            messagebox.showerror("缺少名稱", "請輸入顯示名稱", parent=self)
            return
        self.result = {
            "folder": self._folder,
            "label": self.v_label.get().strip(),
            "cover": self.v_cover.get().strip() or None,
        }
        self.destroy()


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("EasyRPG → 遊戲庫（網頁版/PWA）打包工具")
        self.log_q: queue.Queue = queue.Queue()
        self.games: list = []

        self.lib_name = tk.StringVar(value="我的遊戲庫")
        self.icon = tk.StringVar(value=str(core.DEFAULT_ICON))
        self.soundfont = tk.StringVar(value=str(core.DEFAULT_SOUNDFONT))
        self.out = tk.StringVar(value="dist")
        self.deploy = tk.BooleanVar(value=False)
        self.refresh = tk.BooleanVar(value=False)

        self._build_ui()
        self.root.after(100, self._drain_log)

    def _build_ui(self):
        f = ttk.Frame(self.root, padding=10)
        f.grid(sticky="nsew")

        top = ttk.Frame(f)
        top.grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Label(top, text="遊戲庫名稱").grid(row=0, column=0, padx=4)
        ttk.Entry(top, textvariable=self.lib_name, width=24).grid(row=0, column=1, padx=4)
        ttk.Label(top, text="App 圖示").grid(row=0, column=2, padx=4)
        ttk.Entry(top, textvariable=self.icon, width=28).grid(row=0, column=3, padx=4)
        ttk.Button(top, text="…", width=3,
                   command=lambda: self._pick_file(self.icon)).grid(row=0, column=4)

        self.tree = ttk.Treeview(f, columns=("label", "folder", "cover"),
                                 show="headings", height=8)
        for col, txt, w in [("label", "名稱", 140), ("folder", "資料夾", 320),
                            ("cover", "封面", 120)]:
            self.tree.heading(col, text=txt)
            self.tree.column(col, width=w)
        self.tree.grid(row=1, column=0, sticky="nsew")

        btns = ttk.Frame(f)
        btns.grid(row=2, column=0, sticky="w", pady=4)
        ttk.Button(btns, text="＋ 加入遊戲", command=self._add).pack(side="left", padx=2)
        ttk.Button(btns, text="編輯", command=self._edit).pack(side="left", padx=2)
        ttk.Button(btns, text="移除", command=self._remove).pack(side="left", padx=2)
        ttk.Button(btns, text="↑", width=3, command=lambda: self._move(-1)).pack(side="left", padx=2)
        ttk.Button(btns, text="↓", width=3, command=lambda: self._move(1)).pack(side="left", padx=2)

        opt = ttk.Frame(f)
        opt.grid(row=3, column=0, sticky="w", pady=4)
        ttk.Label(opt, text="音色 SF2").grid(row=0, column=0, padx=4)
        ttk.Entry(opt, textvariable=self.soundfont, width=34).grid(row=0, column=1, padx=4)
        ttk.Button(opt, text="…", width=3,
                   command=lambda: self._pick_file(self.soundfont)).grid(row=0, column=2)
        ttk.Label(opt, text="輸出夾").grid(row=0, column=3, padx=4)
        ttk.Entry(opt, textvariable=self.out, width=14).grid(row=0, column=4, padx=4)

        chk = ttk.Frame(f)
        chk.grid(row=4, column=0, sticky="w")
        ttk.Checkbutton(chk, text="完成後部署到 GitHub Pages",
                        variable=self.deploy).pack(side="left", padx=4)
        ttk.Checkbutton(chk, text="強制更新 web player",
                        variable=self.refresh).pack(side="left", padx=4)

        self.run_btn = ttk.Button(f, text="開始打包遊戲庫", command=self._run)
        self.run_btn.grid(row=5, column=0, sticky="w", pady=6)
        self.log = ScrolledText(f, width=78, height=14, state="disabled")
        self.log.grid(row=6, column=0, pady=6)

    # --- 清單操作 ---
    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for g in self.games:
            cover = Path(g["cover"]).name if g.get("cover") else "（預設）"
            self.tree.insert("", "end", values=(g["label"], str(g["folder"]), cover))

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.index(sel[0])

    def _add(self):
        folder = filedialog.askdirectory(title="選擇遊戲資料夾")
        if not folder:
            return
        dlg = GameDialog(self.root, folder)
        self.root.wait_window(dlg)
        if dlg.result:
            self.games.append(dlg.result)
            self._refresh_tree()

    def _edit(self):
        i = self._selected_index()
        if i is None:
            return
        g = self.games[i]
        dlg = GameDialog(self.root, g["folder"], g["label"], g.get("cover") or "")
        self.root.wait_window(dlg)
        if dlg.result:
            self.games[i] = dlg.result
            self._refresh_tree()

    def _remove(self):
        i = self._selected_index()
        if i is None:
            return
        del self.games[i]
        self._refresh_tree()

    def _move(self, delta):
        i = self._selected_index()
        if i is None:
            return
        j = i + delta
        if 0 <= j < len(self.games):
            self.games[i], self.games[j] = self.games[j], self.games[i]
            self._refresh_tree()
            self.tree.selection_set(self.tree.get_children()[j])

    def _pick_file(self, var):
        p = filedialog.askopenfilename()
        if p:
            var.set(p)

    # --- 打包 ---
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
        if not self.games:
            messagebox.showerror("沒有遊戲", "請先用「＋ 加入遊戲」加至少一個遊戲")
            return
        self.run_btn.configure(state="disabled")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            out = core.build_library(
                games=list(self.games),
                app_label=self.lib_name.get() or "我的遊戲庫",
                app_icon=self.icon.get() or None,
                soundfont=self.soundfont.get() or None,
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

- [ ] **Step 4: 跑 smoke 測試與全部測試**

Run: `python -m pytest -q`
Expected: 全部 PASS。

- [ ] **Step 5: 手動開一次 GUI 確認版面（建議）**

Run: `python easyrpg_web_gui.py`
Expected: 視窗開啟，可「＋ 加入遊戲」選夾→填名稱/封面→列表出現；可移除/排序；關閉即可。

- [ ] **Step 6: Commit**

```bash
git add easyrpg_web_gui.py tests/test_gui_smoke.py
git commit -m "feat: GUI 改寫成遊戲庫清單編輯器（Treeview）"
```

---

### Task 6: 端對端真實驗證（兩個遊戲）

**Files:** 無（驗證用）

- [ ] **Step 1: 跑全部單元測試**

Run: `python -m pytest -q`
Expected: 全部 PASS。

- [ ] **Step 2: 用既有遊戲複製成兩份當測試庫**

Run:
```bash
cd /c/opensource/easyRPG-web
rm -rf /tmp/lib && mkdir -p /tmp/lib
cp -r "C:/opensource/easyRPG/game" /tmp/lib/GameA
cp -r "C:/opensource/easyRPG/game" /tmp/lib/GameB
```

- [ ] **Step 3: 用 Python 直接呼叫 build_library 真打包**

Run:
```bash
cd /c/opensource/easyRPG-web && python -c "
import easyrpg_web_build as core
core.build_library(
    games=[
        {'folder': r'/tmp/lib/GameA', 'label': '遊戲A', 'cover': None},
        {'folder': r'/tmp/lib/GameB', 'label': '遊戲B', 'cover': None},
    ],
    app_label='測試遊戲庫', out='dist',
)
print('OK')
"
```
Expected: 印出各階段並 `OK`；`dist/index.html`(網格)、`dist/play.html`、`dist/games/遊戲A/index.json`、`dist/games/遊戲B/index.json`、`manifest.webmanifest`、`service-worker.js` 皆存在。

- [ ] **Step 4: 本機起伺服器並驗證**

Run:
```bash
cd /c/opensource/easyRPG-web/dist && python -m http.server 8124
```
（背景執行；用畢務必用 `Stop-Process` 或記住 PID `kill` 掉，避免鎖住 dist。）

curl 檢查：
```bash
for p in "/" "/play.html" "/manifest.webmanifest" "/service-worker.js"; do
  curl -s -o /dev/null -w "%{http_code} $p\n" "http://localhost:8124$p"
done
curl -s http://localhost:8124/ | grep -c 'class="card"'   # 應為 2
```
Expected: 全 200；網格 2 張卡。瀏覽器開 `http://localhost:8124` 應見「測試遊戲庫」網格，點任一張進入該遊戲。

- [ ] **Step 5: 收尾**

```bash
git add -A
git commit --allow-empty -m "chore: 多遊戲庫端對端驗證通過（網格選單 + 兩遊戲可啟動）"
```

---

## 自我審查結果（對照 spec）

- **Spec 覆蓋：** 圖示網格選單（Task 2）、多遊戲 staging 各自 gencache + 封面（Task 3）、`play.html` 改名 + `build_library` + manifest/SW（Task 4）、唯一安全 slug 保留 CJK（Task 1）、非法遊戲中止並指名 + 空清單拒絕（Task 4 測試）、GUI 清單編輯器（加入/編輯/移除/排序/封面）（Task 5）、端對端兩遊戲驗證（Task 6）。重用既有模組、保留單一遊戲 `build()`（Task 4 全測試不退步）。✔
- **Placeholder 掃描：** 無 TBD/TODO；每段含完整可執行碼與預期輸出。Task 5 Step 2 已註明 smoke 測試屬「不退步保護」而非紅燈驅動，並說明原因。✔
- **型別/簽章一致性：** `slugify.slugify(name, taken)`、`menu.write_menu(dist, app_label, entries, icon_rel)`（entries 元素 `{label, slug, cover_rel}`）、`library.stage_library(out, games, *, soundfont, ignore_globs)`（games 元素 `{folder, label, slug, cover}`，回傳 entries）、`core.build_library(games=[{folder,label,cover}], app_label, app_icon, soundfont, out, ignore, refresh_player, deploy, player_cache, player_url, log)`、`_validate_game(game, label=None)`、`pwa._pwa_head/install_icon/patch_index_html/write_manifest/write_service_worker/ICON_REL` 在各 task 間一致。✔
- **已知風險：** 重用 `pwa._pwa_head`（底線私有）跨模組 → 同專案內可接受，已於 menu.py 註明用途。`play.html?game=` 依賴 player 由 query string 取遊戲名（與 HTML 檔名無關）→ Task 6 真實驗證。封面以 `cover.png` 命名不論原副檔名，瀏覽器依內容判讀 → 可接受。✔
