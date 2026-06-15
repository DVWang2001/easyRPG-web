# 每遊戲靜態播放頁 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 為每個遊戲產生靜態的 `play-<slug>.html`（標題＝遊戲名、favicon＝封面靜態寫在 head、遊戲 baked-in），讓 iOS Safari 也能換 icon；網格選單改連這些頁，移除上一版的 JS 注入作法。

**Architecture:** `pwa.write_game_pages(dist, entries, icon_rel)` 以既有 `play.html`（patch 過的 player）為模板，對每個遊戲產出 `play-<slug>.html`（換 `<title>`、注入 `<link rel="icon">`/apple-touch-icon、把 `game: undefined` 改成 `game: "<slug>"`）。`menu.py` 的卡片改連 `play-<slug>.html`。`build_library` 以 `write_game_pages` 取代 `inject_play_game_info`。

**Tech Stack:** Python 3.8+（標準庫：`json`/`re`/`html`/`pathlib`）；pytest。

**Spec:** `docs/superpowers/specs/2026-06-16-per-game-play-pages-design.md`
**專案根目錄：** `C:\opensource\easyRPG-web\`（分支 `feat/per-game-play-pages`）

> 任務順序刻意讓「每個任務做完全部測試都綠」：先加新函式（Task 1）→ 接線並移除舊注入（Task 2）→ 改選單連結（Task 3）。

---

### Task 1: `pwa.write_game_pages`（新增，先不接線）

**Files:** `pwa.py`（加 `import re` + append 函式）、`tests/test_pwa_gamepages.py`（新增）

- [ ] **Step 1: 建 `tests/test_pwa_gamepages.py`（失敗測試）**

```python
from pathlib import Path

import pwa

TEMPLATE = (
    "<html><head><title>EasyRPG Player</title></head>"
    "<body><script>createEasyRpgPlayer({ game: undefined, saveFs: undefined });"
    "</script></body></html>"
)


def _write_template(dist: Path):
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "play.html").write_text(TEMPLATE, encoding="utf-8")


def test_write_game_pages_titles_icons_and_baked_game(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    entries = [
        {"label": "花嫁之冠", "slug": "game", "cover_rel": "games/game/cover.png"},
        {"label": "勇者傳說", "slug": "game-2", "cover_rel": None},
    ]

    pwa.write_game_pages(dist, entries)

    a = (dist / "play-game.html").read_text(encoding="utf-8")
    b = (dist / "play-game-2.html").read_text(encoding="utf-8")
    # 靜態標題（取代原 EasyRPG Player）
    assert "<title>花嫁之冠</title>" in a
    assert "EasyRPG Player" not in a
    assert "<title>勇者傳說</title>" in b
    # 靜態 favicon：有封面用封面、沒封面用庫主圖示
    assert '<link rel="icon" href="games/game/cover.png">' in a
    assert 'rel="apple-touch-icon" href="games/game/cover.png"' in a
    assert '<link rel="icon" href="icons/icon.png">' in b
    # 遊戲 baked-in
    assert 'game: "game"' in a
    assert 'game: "game-2"' in b


def test_write_game_pages_escapes_label(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    entries = [{"label": "A & B", "slug": "g", "cover_rel": None}]

    pwa.write_game_pages(dist, entries)

    html = (dist / "play-g.html").read_text(encoding="utf-8")
    assert "<title>A &amp; B</title>" in html
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_gamepages.py -v`
Expected: FAIL（`AttributeError: module 'pwa' has no attribute 'write_game_pages'`）

- [ ] **Step 3a: 在 `pwa.py` 頂部 import 區加入 `import re`**

把頂部：
```python
import json
import shutil
from pathlib import Path
```
改成：
```python
import json
import re
import shutil
from pathlib import Path
```

- [ ] **Step 3b: 在 `pwa.py` 末尾 append `write_game_pages`**

（`json` 在頂部、`_html`（`import html as _html`）在檔案中段已 import，函式定義在其後可用。）
```python

def write_game_pages(dist, entries, icon_rel=ICON_REL) -> None:
    """以 dist/play.html 為模板，為每個遊戲產出 play-<slug>.html：
    靜態 <title>＝遊戲名、<link rel=icon>＝封面（無封面用主圖示）、game baked-in。
    icon 靜態寫在 head → iOS Safari 也能換分頁圖示。"""
    dist = Path(dist)
    template = (dist / "play.html").read_text(encoding="utf-8")
    for e in entries:
        slug = e["slug"]
        cover = e.get("cover_rel") or icon_rel
        cover_esc = _html.escape(cover, quote=True)
        html = template.replace("game: undefined", "game: " + json.dumps(slug))
        new_head = (
            "\n<title>" + _html.escape(e["label"]) + "</title>"
            '\n<link rel="icon" href="' + cover_esc + '">'
            '\n<link rel="apple-touch-icon" href="' + cover_esc + '">\n'
        )
        html = re.sub(r"<title>.*?</title>", "", html, count=1, flags=re.S)
        html = html.replace("</head>", new_head + "</head>", 1)
        (dist / ("play-" + slug + ".html")).write_text(html, encoding="utf-8")
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_gamepages.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 跑全部測試（不退步）**

Run: `python -m pytest -q`
Expected: 全部 PASS（原 44 + 新 2 = 46；`write_game_pages` 尚未接線、`inject_play_game_info` 仍在）。

- [ ] **Step 6: Commit**

```bash
git add pwa.py tests/test_pwa_gamepages.py
git commit -m "feat: pwa.write_game_pages（每遊戲靜態播放頁，title/icon 寫死 head）"
```

---

### Task 2: 接線 `build_library` 並移除舊 JS 注入

**Files:** `easyrpg_web_build.py`（改一行）、`pwa.py`（移除 `inject_play_game_info`）、`tests/test_pwa_inject.py`（刪除）、`tests/test_build_library.py`（改 fixture + 換測試）

- [ ] **Step 1: 改 `tests/test_build_library.py` 的假 player（讓模板含可被改寫的 title 與 game）**

把檔案頂部 `_fake_player_tarball` 中 index.html 那一行：
```python
            ("index.html", b"<html><head></head><body></body></html>"),
```
改成：
```python
            ("index.html", b"<html><head><title>EasyRPG Player</title></head><body><script>createEasyRpgPlayer({ game: undefined, saveFs: undefined });</script></body></html>"),
```

- [ ] **Step 2: 刪除舊測試、換成每遊戲頁測試**

在 `tests/test_build_library.py` 中，**刪除**整個 `test_build_library_injects_play_game_info` 函式，**新增**：
```python
def test_build_library_per_game_page(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    g1 = tmp_path / "Hanayome"
    _game(g1, "1")
    cover = tmp_path / "c.png"
    cover.write_bytes(b"\x89PNG")
    out = tmp_path / "dist"

    core.build_library(
        games=[{"folder": g1, "label": "花嫁之冠", "cover": cover}],
        app_icon=None, soundfont=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )

    page = (out / "play-game.html").read_text(encoding="utf-8")  # 花嫁之冠 → slug "game"
    assert "<title>花嫁之冠</title>" in page
    assert '<link rel="icon" href="games/game/cover.png">' in page
    assert 'game: "game"' in page
```

- [ ] **Step 3: 跑這兩個相關測試確認失敗**

Run: `python -m pytest tests/test_build_library.py::test_build_library_per_game_page -v`
Expected: FAIL（`build_library` 還沒呼叫 `write_game_pages` → `play-game.html` 不存在）。

- [ ] **Step 4: 改 `easyrpg_web_build.py` 的 `build_library`**

找到這行（上一版加的）：
```python
    pwa.inject_play_game_info(out, entries)             # play.html 依 ?game 設標題與 favicon
```
改成：
```python
    pwa.write_game_pages(out, entries, icon_rel)        # 每遊戲靜態頁 play-<slug>.html（title/icon 寫死）
```

- [ ] **Step 5: 移除 `pwa.py` 的 `inject_play_game_info`**

把 `pwa.py` 中整個 `def inject_play_game_info(dist, entries) -> Path:` 函式（含其 docstring 與內容）刪除。（`write_game_pages` 已取代它。）

- [ ] **Step 6: 刪除過時測試檔**

Run: `git rm tests/test_pwa_inject.py`

- [ ] **Step 7: 跑全部測試（不退步）**

Run: `python -m pytest -q`
Expected: 全部 PASS（46 − 2 刪除 + 0 = 44；`test_pwa_inject.py` 的 2 個移除、`inject` 端對端測試換成 per_game_page）。實際數字以執行結果為準，重點是**全綠、無 `inject` 殘留參照**。

- [ ] **Step 8: 確認沒有殘留參照**

Run: `grep -rn "inject_play_game_info" . --include=*.py`
Expected: 無輸出（函式與呼叫都已移除）。

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: build_library 改用 write_game_pages，移除 inject_play_game_info"
```

---

### Task 3: 網格選單改連 `play-<slug>.html`

**Files:** `menu.py`、`tests/test_menu.py`、`tests/test_build_library.py`（改 `two_games` href 斷言）

- [ ] **Step 1: 改 `tests/test_menu.py` 的 `test_write_menu_generates_grid`**

把該測試整個換成（slug 改用實際會出現的 ASCII，href 改斷言 `play-<slug>.html`）：
```python
def test_write_menu_generates_grid(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    entries = [
        {"label": "花嫁之冠", "slug": "game", "cover_rel": "games/game/cover.png"},
        {"label": "A & B", "slug": "a-b", "cover_rel": None},
    ]

    out = menu.write_menu(dist, "我的遊戲庫", entries)

    assert out == dist / "index.html"
    html = out.read_text(encoding="utf-8")
    assert "我的遊戲庫" in html
    assert 'href="play-game.html"' in html
    assert 'href="play-a-b.html"' in html
    assert "games/game/cover.png" in html
    assert "icons/icon.png" in html      # 第二個無封面 → 用主圖示
    assert "A &amp; B" in html           # label 經 HTML 跳脫
    assert 'rel="manifest"' in html
    assert "serviceWorker" in html
```

- [ ] **Step 2: 跑該測試確認失敗**

Run: `python -m pytest tests/test_menu.py::test_write_menu_generates_grid -v`
Expected: FAIL（目前 href 還是 `play.html?game=...`）。

- [ ] **Step 3: 改 `menu.py`**

把 `menu.py` 頂部 import（若有 `from urllib.parse import quote`）移除該行（改用後不再需要）。
把 `write_menu` 內這段：
```python
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
```
改成（href 改為 `play-<slug>.html`，slug 為 ASCII，免 URL 編碼）：
```python
    cards = []
    for e in entries:
        href = "play-" + e["slug"] + ".html"
        cover = e["cover_rel"] or icon_rel
        card = (
            _CARD.replace("__HREF__", _html.escape(href, quote=True))
            .replace("__COVER__", _html.escape(cover, quote=True))
            .replace("__LABEL__", _html.escape(e["label"]))
        )
        cards.append(card)
```

- [ ] **Step 4: 跑該測試確認通過**

Run: `python -m pytest tests/test_menu.py::test_write_menu_generates_grid -v`
Expected: PASS。

- [ ] **Step 5: 改 `tests/test_build_library.py` 的 `test_build_library_two_games` href 斷言**

在該測試中，把這段：
```python
    assert "play.html?game=" in grid
    assert grid.count('class="card"') == 2
    # CJK 顯示名稱仍出現在網格，但資料夾 slug 是 ASCII（player 的 ?game= 不解碼）
    assert "花嫁之冠" in grid
    assert "勇者傳說" in grid
    assert (out / "games" / "game" / "index.json").exists()
    assert (out / "games" / "game-2" / "index.json").exists()
    # 網格連結必須是純 ASCII 的 ?game=
    import re as _re
    for href in _re.findall(r'href="(play\.html\?game=[^"]*)"', grid):
        assert href.isascii()
```
換成：
```python
    assert grid.count('class="card"') == 2
    assert "花嫁之冠" in grid
    assert "勇者傳說" in grid
    # 網格連到每遊戲靜態頁，且各頁存在
    assert 'href="play-game.html"' in grid
    assert 'href="play-game-2.html"' in grid
    assert (out / "play-game.html").exists()
    assert (out / "play-game-2.html").exists()
    assert (out / "games" / "game" / "index.json").exists()
    assert (out / "games" / "game-2" / "index.json").exists()
```

- [ ] **Step 6: 跑全部測試（不退步）**

Run: `python -m pytest -q`
Expected: 全部 PASS。

- [ ] **Step 7: 真實建置煙霧驗證（用既有遊戲）**

Run（確認 player 真有 `game: undefined` 可改寫；若無，baked game 會失效需回報）：
```bash
cd /c/opensource/easyRPG-web
rm -rf /c/opensource/_pgtest && mkdir -p /c/opensource/_pgtest && cp -r "C:/opensource/easyRPG/game" /c/opensource/_pgtest/GameA
python -c "
import easyrpg_web_build as core
core.build_library(games=[{'folder': r'C:/opensource/_pgtest/GameA', 'label': '測試遊戲', 'cover': None}], app_label='庫', out='dist')
from pathlib import Path
import glob
pages = glob.glob('dist/play-*.html')
print('per-game pages:', pages)
t = Path(pages[0]).read_text(encoding='utf-8')
print('has baked game:', 'game: \"' in t)
print('has static title:', '<title>測試遊戲</title>' in t)
"
rm -rf /c/opensource/_pgtest
```
Expected: 印出一個 `dist/play-測試遊戲...`（slug 為 ASCII，例如 `play-.html` 退回 → 其實「測試遊戲」純中文 → slug `game`，故 `dist/play-game.html`）；`has baked game: True`、`has static title: True`。若 `has baked game: False`，表示真實 player 的字串不是 `game: undefined`，**回報 DONE_WITH_CONCERNS**（需調整替換字串），不要硬過。

- [ ] **Step 8: 清理建置產物並 Commit**

```bash
rm -rf dist
git add menu.py tests/test_menu.py tests/test_build_library.py
git commit -m "feat: 網格選單改連每遊戲靜態頁 play-<slug>.html"
```

---

## 自我審查結果（對照 spec）

- **Spec 覆蓋：** `write_game_pages` 產生 `play-<slug>.html`、靜態 title/icon/apple-touch、baked-in game、無封面用主圖示、label 跳脫（Task 1）；`build_library` 接線、移除 `inject_play_game_info`、刪舊測試（Task 2）；`menu` 改連 `play-<slug>.html`（Task 3）；真實 player `game: undefined` 假設由 Task 3 Step 7 煙霧驗證。✔
- **Placeholder 掃描：** 無 TBD/TODO；每步含完整可執行碼與預期輸出。✔
- **一致性：** `write_game_pages(dist, entries, icon_rel=ICON_REL)`、entries 元素 `{label, slug, cover_rel}`、輸出 `play-<slug>.html`、menu href `play-<slug>.html`、build_library 在 `menu.write_menu` 後呼叫 `write_game_pages`（取代 inject）、SW 仍最後（precache 含各遊戲頁）。✔
- **任務間綠燈：** Task 1 只新增（46）；Task 2 接線＋刪除（全綠、無殘留參照）；Task 3 改 menu＋斷言（全綠）。✔
