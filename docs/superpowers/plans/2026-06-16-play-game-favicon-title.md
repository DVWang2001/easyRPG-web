# play.html 標題＝遊戲名、favicon＝封面 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 點進某遊戲（`play.html?game=<slug>`）後，分頁標題變成該遊戲名稱、favicon 變成該遊戲封面；沒封面則維持遊戲庫主圖示。

**Architecture:** 在 `pwa.py` 新增 `inject_play_game_info(dist, entries)`，把一份 `slug → {name, cover?}` 對照表與一小段切換 script 注入 `play.html`。`build_library` 在算出 entries（label/slug/cover_rel）後呼叫它。不動 `library.py`、不加網址參數（避免 player 的 parseArgs 誤把它當 CLI 參數）。

**Tech Stack:** Python 3.8+（標準庫，`pwa.py` 頂部已 `import json`）；pytest。

**Spec:** `docs/superpowers/specs/2026-06-16-play-game-favicon-title-design.md`
**專案根目錄：** `C:\opensource\easyRPG-web\`（分支 `feat/play-game-favicon-title`）

---

## 檔案結構

| 檔案 | 變更 | 職責 |
|---|---|---|
| `pwa.py` | 新增函式 | `inject_play_game_info(dist, entries)`：把對照表＋script 注入 `dist/play.html` |
| `easyrpg_web_build.py` | `build_library` 加一行 | `menu.write_menu(...)` 之後呼叫 `pwa.inject_play_game_info(out, entries)` |
| `tests/test_pwa_inject.py` | 新增 | 注入函式單元測試 |
| `tests/test_build_library.py` | 加測試 | 端對端：play.html 含遊戲名與封面路徑 |

---

### Task 1: `pwa.inject_play_game_info`

**Files:** `pwa.py`（append 函式）、`tests/test_pwa_inject.py`（新增）

- [ ] **Step 1: 建 `tests/test_pwa_inject.py`（失敗測試）**

```python
from pathlib import Path

import pwa


def test_inject_play_game_info(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "play.html").write_text(
        "<html><head></head><body></body></html>", encoding="utf-8"
    )
    entries = [
        {"label": "花嫁之冠", "slug": "game", "cover_rel": "games/game/cover.png"},
        {"label": "勇者傳說", "slug": "game-2", "cover_rel": None},
    ]

    out = pwa.inject_play_game_info(dist, entries)

    assert out == dist / "play.html"
    html = (dist / "play.html").read_text(encoding="utf-8")
    # 對照表與兩個遊戲名稱
    assert "__EASYRPG_GAMES__" in html
    assert "花嫁之冠" in html
    assert "勇者傳說" in html
    # 有封面者帶 cover 路徑；無封面者不帶
    assert "games/game/cover.png" in html
    assert "games/game-2" not in html
    # 切換邏輯：設標題 + 設 favicon
    assert "document.title" in html
    assert "icon" in html
    assert html.count("</head>") == 1  # 沒破壞結構


def test_inject_escapes_angle_bracket(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "play.html").write_text("<head></head>", encoding="utf-8")
    entries = [{"label": "a</script>b", "slug": "g", "cover_rel": None}]

    pwa.inject_play_game_info(dist, entries)

    html = (dist / "play.html").read_text(encoding="utf-8")
    # 名稱裡的 < 必須轉義，不能出現真正的 </script>（除了我們自己的結尾那一個）
    assert "a\\u003c/script>b" in html
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_inject.py -v`
Expected: FAIL（`AttributeError: module 'pwa' has no attribute 'inject_play_game_info'`）

- [ ] **Step 3: 在 `pwa.py` 末尾 append**

（`pwa.py` 頂部已 `import json` 與 `from pathlib import Path`，不要重複 import）
```python

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
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_inject.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 跑全部測試（不退步）**

Run: `python -m pytest -q`
Expected: 全部 PASS（原 41 + 新 2 = 43）。

- [ ] **Step 6: Commit**

```bash
git add pwa.py tests/test_pwa_inject.py
git commit -m "feat: inject_play_game_info（play.html 依遊戲設標題與 favicon）"
```

---

### Task 2: 把注入接進 `build_library`

**Files:** `easyrpg_web_build.py`（`build_library` 加一行）、`tests/test_build_library.py`（加測試）

- [ ] **Step 1: 在 `tests/test_build_library.py` 末尾新增失敗測試**

（檔案頂部已有 `_fake_player_tarball` 與 `_game` 輔助函式，沿用。）
```python
def test_build_library_injects_play_game_info(tmp_path):
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

    play = (out / "play.html").read_text(encoding="utf-8")
    assert "__EASYRPG_GAMES__" in play
    assert "花嫁之冠" in play            # 遊戲名（顯示名稱保留中文）
    assert "games/game/cover.png" in play  # 「花嫁之冠」slug 退回 ASCII "game"，封面在此
    assert "document.title" in play
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_build_library.py::test_build_library_injects_play_game_info -v`
Expected: FAIL（play.html 尚未注入 → 找不到 `__EASYRPG_GAMES__`）。

- [ ] **Step 3: 在 `easyrpg_web_build.py` 的 `build_library` 加一行**

找到這段（在 build_library 內）：
```python
    _log("產生遊戲庫選單…", log)
    menu.write_menu(out, app_label, entries, icon_rel)  # 寫新的 index.html（網格）

    pwa.write_manifest(out, app_label, icon_rel)
    pwa.write_service_worker(out)                        # 最後：precache 全部資產
```
改成（在 menu 之後、manifest 之前插入注入呼叫）：
```python
    _log("產生遊戲庫選單…", log)
    menu.write_menu(out, app_label, entries, icon_rel)  # 寫新的 index.html（網格）
    pwa.inject_play_game_info(out, entries)             # play.html 依 ?game 設標題與 favicon

    pwa.write_manifest(out, app_label, icon_rel)
    pwa.write_service_worker(out)                        # 最後：precache 全部資產
```
（其餘不動。）

- [ ] **Step 4: 跑該測試確認通過**

Run: `python -m pytest tests/test_build_library.py::test_build_library_injects_play_game_info -v`
Expected: PASS。

- [ ] **Step 5: 跑全部測試（不退步）**

Run: `python -m pytest -q`
Expected: 全部 PASS（44）。

- [ ] **Step 6: Commit**

```bash
git add easyrpg_web_build.py tests/test_build_library.py
git commit -m "feat: build_library 注入 play.html 遊戲標題/favicon 對照表"
```

---

## 自我審查結果（對照 spec）

- **Spec 覆蓋：** 注入對照表＋script（Task 1）、依 `?game` 設 `document.title` 與 favicon、封面 onload 才換的 fallback、`<` 轉義防 `</script>`、無封面不帶 cover（Task 1 測試 `games/game-2` 不出現）、build_library 在正確順序注入（Task 2，menu 之後、SW 之前）、單一遊戲 build() 不受影響（未呼叫）。✔
- **Placeholder 掃描：** 無 TBD/TODO；每步含完整可執行碼與預期輸出。✔
- **一致性：** `inject_play_game_info(dist, entries)`、entries 元素 `{label, slug, cover_rel}`、map 值 `{name, cover?}`、注入點在 `menu.write_menu` 後 / `write_manifest` 前、SW 最後（會 precache 含注入的 play.html）。✔
- **既有行為：** entries 由既有 `library.stage_library` 回傳，介面不變；`library.py` 不動。✔
