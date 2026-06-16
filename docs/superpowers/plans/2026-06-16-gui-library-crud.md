# GUI 遊戲庫增刪查改 ＋ 一鍵部署 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把無狀態的打包 GUI 改成持久化遊戲庫編輯器：以遊戲專案為單位做增刪查改（存進 `library.json`），開窗自動載入、變動自動存檔，並用單一主按鈕「重建並部署到網頁」；首次從線上 gh-pages 產草稿、部署前擋空資料夾。

**Architecture:** 新增兩個純函式模組 `project.py`（`library.json` 載入/儲存 ＋ 安全閥 `missing_sources`）與 `bootstrap.py`（從部署的 `index.html` 解析草稿）。`easyrpg_web_gui.py` 改成載入/自動存檔，主按鈕呼叫既有 `core.build_library(..., deploy=True)`。**build 核心 `easyrpg_web_build.py` 完全不動**（沿用全量重建＋force-push）。

**Tech Stack:** Python 3.8+（標準庫：`json`/`os`/`re`/`html`/`pathlib`/`tkinter`）；pytest。

**Spec:** `docs/superpowers/specs/2026-06-16-gui-library-crud-design.md`
**專案根目錄：** `C:\opensource\easyRPG-web\`（分支 `feat/gui-library-crud`）

## 檔案結構

- **Create `project.py`** — `library.json` 的 schema 預設、載入（容錯）、原子儲存、部署前安全閥。純函式、無 Tkinter。
- **Create `bootstrap.py`** — 解析部署的 `index.html` 選單 → 草稿專案 dict。純函式、不碰 git/網路。
- **Modify `easyrpg_web_gui.py`** — 載入專案（查）、加入/編輯/移除/排序皆自動存檔（增改刪）、`GameDialog` 加原始資料夾欄、主按鈕「重建並部署到網頁」＋部署前安全閥。
- **Modify `.gitignore`** — 加入 `library.json`（含本機絕對路徑，不進版控）。
- **Create `tests/test_project.py`**、**`tests/test_bootstrap.py`**；**Modify `tests/test_gui_smoke.py`**。

> 任務順序讓每個任務做完全部測試都綠：先純函式模組（Task 1–3）→ 再接 GUI（Task 4）→ 最後一次性產草稿（Task 5）。

---

### Task 1: `project.py` — 載入/儲存（持久層）

**Files:**
- Create: `project.py`
- Test: `tests/test_project.py`

- [ ] **Step 1: 寫失敗測試 `tests/test_project.py`**

```python
import json

import project


def test_default_project_shape():
    p = project.default_project()
    assert p["version"] == project.VERSION
    assert p["games"] == []
    assert p["out"] == "dist"
    assert isinstance(p["lib_name"], str)


def test_load_missing_returns_default_no_warning(tmp_path):
    proj, warning = project.load_project(tmp_path / "nope.json")
    assert warning is None
    assert proj["games"] == []


def test_load_corrupt_returns_default_with_warning(tmp_path):
    f = tmp_path / "library.json"
    f.write_text("{ not valid json", encoding="utf-8")
    proj, warning = project.load_project(f)
    assert proj["games"] == []
    assert warning is not None  # 不丟例外


def test_load_fills_missing_fields(tmp_path):
    f = tmp_path / "library.json"
    f.write_text(json.dumps({"lib_name": "只給名稱"}), encoding="utf-8")
    proj, warning = project.load_project(f)
    assert warning is None
    assert proj["lib_name"] == "只給名稱"
    assert proj["out"] == "dist"        # 補回預設
    assert proj["games"] == []


def test_save_then_load_roundtrip(tmp_path):
    f = tmp_path / "library.json"
    data = {
        "version": 1, "lib_name": "我的庫", "icon": "i.png",
        "soundfont": "s.sf2", "out": "dist",
        "games": [{"folder": "C:/g/甲", "label": "花嫁之冠", "cover": None, "rtp": None}],
    }
    project.save_project(f, data)
    # 中文不被跳脫成 \uXXXX
    assert "花嫁之冠" in f.read_text(encoding="utf-8")
    proj, warning = project.load_project(f)
    assert warning is None
    assert proj["games"][0]["label"] == "花嫁之冠"
    assert proj["games"][0]["cover"] is None


def test_save_is_atomic_no_tmp_left(tmp_path):
    f = tmp_path / "library.json"
    project.save_project(f, project.default_project())
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "library.json"]
    assert leftovers == []
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_project.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'project'`）

- [ ] **Step 3: 建立 `project.py`**

```python
# project.py
"""遊戲庫專案檔（library.json）的載入/儲存與安全閥 —— 純函式，與 GUI 隔離。"""
from __future__ import annotations

import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ICON = HERE / "assets" / "app_icon.png"
DEFAULT_SOUNDFONT = HERE / "assets" / "easyrpg.soundfont"

VERSION = 1


def default_project() -> dict:
    """完整 schema 的空專案。"""
    return {
        "version": VERSION,
        "lib_name": "我的遊戲庫",
        "icon": str(DEFAULT_ICON),
        "soundfont": str(DEFAULT_SOUNDFONT),
        "out": "dist",
        "games": [],
    }


def _normalize(data) -> dict:
    """以 default 為底補齊缺欄位；games 內每筆補齊 folder/label/cover/rtp。"""
    proj = default_project()
    if isinstance(data, dict):
        for k in ("version", "lib_name", "icon", "soundfont", "out"):
            if data.get(k) is not None:
                proj[k] = data[k]
        games = data.get("games")
        if isinstance(games, list):
            norm = []
            for g in games:
                if not isinstance(g, dict):
                    continue
                norm.append({
                    "folder": g.get("folder") or "",
                    "label": g.get("label") or "",
                    "cover": g.get("cover") or None,
                    "rtp": g.get("rtp") or None,
                })
            proj["games"] = norm
    return proj


def load_project(path):
    """讀 library.json。缺檔→(default, None)；壞檔→(default, 警告字串)。永不丟例外。"""
    path = Path(path)
    if not path.exists():
        return default_project(), None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as e:
        return default_project(), f"讀取 {path.name} 失敗：{e}（已以空庫開啟）"
    return _normalize(raw), None


def save_project(path, data) -> None:
    """原子寫入 library.json（UTF-8、不跳脫中文、縮排 2）。"""
    path = Path(path)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_project.py -v`
Expected: PASS（6 passed）

- [ ] **Step 5: 跑全部測試（不退步）**

Run: `python -m pytest -q`
Expected: 全部 PASS。

- [ ] **Step 6: Commit**

```bash
git add project.py tests/test_project.py
git commit -m "feat: project.py（library.json 載入/原子儲存，容錯）"
```

---

### Task 2: `project.missing_sources` — 部署前安全閥

**Files:**
- Modify: `project.py`（append 函式）
- Test: `tests/test_project.py`（append 測試）

- [ ] **Step 1: 在 `tests/test_project.py` 末尾 append 失敗測試**

```python
def test_missing_sources_flags_empty_and_invalid(tmp_path):
    good = tmp_path / "Good"
    good.mkdir()
    (good / "RPG_RT.ldb").write_bytes(b"x")
    games = [
        {"folder": "", "label": "草稿甲", "cover": None, "rtp": None},
        {"folder": str(tmp_path / "NotExist"), "label": "壞乙", "cover": None, "rtp": None},
        {"folder": str(good), "label": "正常丙", "cover": None, "rtp": None},
    ]
    bad = project.missing_sources(games)
    assert bad == ["草稿甲", "壞乙"]


def test_missing_sources_all_valid_returns_empty(tmp_path):
    g = tmp_path / "G"
    g.mkdir()
    (g / "RPG_RT.lmt").write_bytes(b"x")
    assert project.missing_sources(
        [{"folder": str(g), "label": "丁", "cover": None, "rtp": None}]) == []
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_project.py::test_missing_sources_flags_empty_and_invalid -v`
Expected: FAIL（`AttributeError: module 'project' has no attribute 'missing_sources'`）

- [ ] **Step 3: 在 `project.py` 末尾 append**

```python


def missing_sources(games) -> list:
    """回傳『原始資料夾未指定或無效（缺 RPG_RT.ldb/.lmt）』的遊戲顯示名稱清單。"""
    bad = []
    for g in games:
        folder = (g.get("folder") or "").strip()
        ok = bool(folder) and any(
            (Path(folder) / n).exists() for n in ("RPG_RT.ldb", "RPG_RT.lmt"))
        if not ok:
            bad.append(g.get("label") or folder or "（未命名）")
    return bad
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_project.py -v`
Expected: PASS（8 passed）

- [ ] **Step 5: Commit**

```bash
git add project.py tests/test_project.py
git commit -m "feat: project.missing_sources（部署前擋空/無效資料夾）"
```

---

### Task 3: `bootstrap.py` — 從線上選單產草稿

**Files:**
- Create: `bootstrap.py`
- Test: `tests/test_bootstrap.py`

- [ ] **Step 1: 寫失敗測試 `tests/test_bootstrap.py`**

```python
import bootstrap

# 與 menu.py 產生的卡片格式一致：
#   <a class="card" href="play-<slug>.html"><img src="<cover>" alt=""><span><label></span></a>
MENU = """<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<title>RM作品收藏</title>
</head><body><header>RM作品收藏</header><div class="grid">
<a class="card" href="play-2003-i.html"><img src="games/2003-i/cover.png" alt=""><span>2003月藍傳奇Ｉ～異界來的訪客</span></a>
<a class="card" href="play-game.html"><img src="games/game/cover.png" alt=""><span>花嫁之冠</span></a>
<a class="card" href="play-g.html"><img src="icons/icon.png" alt=""><span>A &amp; B</span></a>
</div></body></html>
"""


def test_draft_parses_title_and_games():
    draft = bootstrap.draft_project_from_menu(MENU)
    assert draft["lib_name"] == "RM作品收藏"
    assert len(draft["games"]) == 3
    labels = [g["label"] for g in draft["games"]]
    assert labels == ["2003月藍傳奇Ｉ～異界來的訪客", "花嫁之冠", "A & B"]  # 實體還原


def test_draft_games_have_empty_folder_and_null_cover():
    draft = bootstrap.draft_project_from_menu(MENU)
    for g in draft["games"]:
        assert g["folder"] == ""
        assert g["cover"] is None
        assert g["rtp"] is None


def test_draft_empty_menu_keeps_title():
    html = "<html><head><title>空庫</title></head><body><div class='grid'></div></body></html>"
    draft = bootstrap.draft_project_from_menu(html)
    assert draft["lib_name"] == "空庫"
    assert draft["games"] == []
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_bootstrap.py -v`
Expected: FAIL（`ModuleNotFoundError: No module named 'bootstrap'`）

- [ ] **Step 3: 建立 `bootstrap.py`**

```python
# bootstrap.py
"""從已部署的選單 index.html 產生草稿 library.json（純函式，不碰 git/網路）。"""
from __future__ import annotations

import html as _html
import re

import project

_TITLE_RE = re.compile(r"<title>(?P<title>.*?)</title>", re.S)
_CARD_RE = re.compile(
    r'<a class="card"[^>]*>.*?<span>(?P<label>.*?)</span>\s*</a>', re.S)


def draft_project_from_menu(html: str) -> dict:
    """解析部署選單 → 草稿專案 dict（folder 留空、cover/rtp 為 None）。"""
    proj = project.default_project()
    m = _TITLE_RE.search(html)
    if m:
        proj["lib_name"] = _html.unescape(m.group("title").strip())
    games = []
    for cm in _CARD_RE.finditer(html):
        label = _html.unescape(cm.group("label").strip())
        games.append({"folder": "", "label": label, "cover": None, "rtp": None})
    proj["games"] = games
    return proj
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_bootstrap.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 跑全部測試（不退步）**

Run: `python -m pytest -q`
Expected: 全部 PASS。

- [ ] **Step 6: Commit**

```bash
git add bootstrap.py tests/test_bootstrap.py
git commit -m "feat: bootstrap.py（從線上選單 index.html 產草稿 library.json）"
```

---

### Task 4: GUI 接線（查 / 增改刪自動存檔 / 一鍵部署 / 安全閥）

**Files:**
- Modify: `easyrpg_web_gui.py`（整檔改寫如下）
- Modify: `tests/test_gui_smoke.py`

- [ ] **Step 1: 改寫 `tests/test_gui_smoke.py`（加載入與自動存檔測試）**

把整個 `tests/test_gui_smoke.py` 換成：
```python
import importlib
import json

import pytest

import easyrpg_web_build as core


def test_gui_imports_and_references_core():
    mod = importlib.import_module("easyrpg_web_gui")
    assert mod.core is core
    assert hasattr(mod, "App")
    assert callable(core.build_library)
    assert callable(core.build)


def _make_root():
    import tkinter as tk
    try:
        return tk.Tk()
    except tk.TclError:
        pytest.skip("此環境無法初始化 Tk（無顯示）")


def test_app_loads_existing_library(tmp_path):
    import easyrpg_web_gui as gui
    lib = tmp_path / "library.json"
    lib.write_text(json.dumps({
        "version": 1, "lib_name": "測試庫", "icon": "i.png",
        "soundfont": "s.sf2", "out": "dist",
        "games": [{"folder": "", "label": "甲", "cover": None, "rtp": None},
                  {"folder": "", "label": "乙", "cover": None, "rtp": None}],
    }, ensure_ascii=False), encoding="utf-8")
    root = _make_root()
    try:
        app = gui.App(root, project_path=lib)
        assert app.lib_name.get() == "測試庫"
        assert len(app.games) == 2
        assert len(app.tree.get_children()) == 2
    finally:
        root.destroy()


def test_app_autosaves_on_mutation(tmp_path):
    import easyrpg_web_gui as gui
    lib = tmp_path / "library.json"
    root = _make_root()
    try:
        app = gui.App(root, project_path=lib)
        app.games.append({"folder": "", "label": "新遊戲", "cover": None, "rtp": None})
        app._refresh_tree()
        app._save()
        text = lib.read_text(encoding="utf-8")
        assert "新遊戲" in text                       # 中文不被跳脫
        data = json.loads(text)
        assert data["games"][-1]["label"] == "新遊戲"
    finally:
        root.destroy()
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_gui_smoke.py -v`
Expected: FAIL（`App.__init__` 還不收 `project_path`、無 `_save`/不會自載入）。

- [ ] **Step 3: 整檔改寫 `easyrpg_web_gui.py`**

把整個 `easyrpg_web_gui.py` 換成：
```python
# easyrpg_web_gui.py
"""easyRPG-web 遊戲庫 GUI（持久化清單編輯器：增刪查改 ＋ 一鍵重建並部署）。"""
from __future__ import annotations

import queue
import threading
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import easyrpg_web_build as core
import project

LIBRARY_JSON = Path(__file__).resolve().parent / "library.json"


class GameDialog(tk.Toplevel):
    """加入/編輯單一遊戲：原始資料夾 + 名稱 + 封面（選填）+ RTP（勾選＋資料夾）。回傳 dict 或 None。"""

    def __init__(self, parent, folder="", label="", cover="", rtp=""):
        super().__init__(parent)
        self.title("遊戲設定")
        self.result = None
        self.transient(parent)
        self.grab_set()

        self.v_folder = tk.StringVar(value=folder)
        self.v_label = tk.StringVar(value=label)
        self.v_cover = tk.StringVar(value=cover)
        self.v_rtp_on = tk.BooleanVar(value=bool(rtp))
        self.v_rtp = tk.StringVar(value=rtp)

        ttk.Label(self, text="原始資料夾").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(self, textvariable=self.v_folder, width=36).grid(row=0, column=1, padx=4)
        ttk.Button(self, text="…", width=3, command=self._pick_folder).grid(row=0, column=2)
        ttk.Label(self, text="顯示名稱").grid(row=1, column=0, sticky="w", padx=8)
        ttk.Entry(self, textvariable=self.v_label, width=36).grid(row=1, column=1, padx=4)
        ttk.Label(self, text="封面圖（選填）").grid(row=2, column=0, sticky="w", padx=8)
        ttk.Entry(self, textvariable=self.v_cover, width=36).grid(row=2, column=1, padx=4)
        ttk.Button(self, text="…", width=3, command=self._pick_cover).grid(row=2, column=2)
        ttk.Checkbutton(self, text="加入 RTP", variable=self.v_rtp_on).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(6, 0))
        ttk.Label(self, text="RTP 資料夾").grid(row=4, column=0, sticky="w", padx=8)
        ttk.Entry(self, textvariable=self.v_rtp, width=36).grid(row=4, column=1, padx=4)
        ttk.Button(self, text="…", width=3, command=self._pick_rtp).grid(row=4, column=2)
        bar = ttk.Frame(self)
        bar.grid(row=5, column=0, columnspan=3, pady=8)
        ttk.Button(bar, text="確定", command=self._ok).pack(side="left", padx=4)
        ttk.Button(bar, text="取消", command=self.destroy).pack(side="left", padx=4)

    def _pick_folder(self):
        d = filedialog.askdirectory(title="選擇遊戲資料夾")
        if d:
            self.v_folder.set(d)
            if not self.v_label.get().strip():
                self.v_label.set(Path(d).name)

    def _pick_cover(self):
        p = filedialog.askopenfilename(
            filetypes=[("圖片", "*.png *.jpg *.jpeg *.gif"), ("全部", "*.*")])
        if p:
            self.v_cover.set(p)

    def _pick_rtp(self):
        d = filedialog.askdirectory(title="選擇 RTP 資料夾")
        if d:
            self.v_rtp.set(d)
            self.v_rtp_on.set(True)

    def _ok(self):
        if not self.v_folder.get().strip():
            messagebox.showerror("缺少資料夾", "請選擇遊戲的原始資料夾", parent=self)
            return
        if not self.v_label.get().strip():
            messagebox.showerror("缺少名稱", "請輸入顯示名稱", parent=self)
            return
        rtp = self.v_rtp.get().strip() if self.v_rtp_on.get() else ""
        self.result = {
            "folder": self.v_folder.get().strip(),
            "label": self.v_label.get().strip(),
            "cover": self.v_cover.get().strip() or None,
            "rtp": rtp or None,
        }
        self.destroy()


class App:
    def __init__(self, root: tk.Tk, project_path=None):
        self.root = root
        root.title("EasyRPG → 遊戲庫（網頁版/PWA）打包工具")
        self.log_q: queue.Queue = queue.Queue()
        self.project_path = Path(project_path) if project_path else LIBRARY_JSON

        proj, warning = project.load_project(self.project_path)
        self.games: list = [dict(g) for g in proj["games"]]
        self.lib_name = tk.StringVar(value=proj["lib_name"])
        self.icon = tk.StringVar(value=proj["icon"])
        self.soundfont = tk.StringVar(value=proj["soundfont"])
        self.out = tk.StringVar(value=proj["out"])
        self.refresh = tk.BooleanVar(value=False)

        self._build_ui()
        self._refresh_tree()

        # 初值設定完才掛 trace，避免初始化時誤觸發寫檔
        for var in (self.lib_name, self.icon, self.soundfont, self.out):
            var.trace_add("write", lambda *_: self._save())

        if warning:
            messagebox.showwarning("讀取專案檔", warning)
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

        self.tree = ttk.Treeview(f, columns=("label", "folder", "cover", "rtp"),
                                 show="headings", height=8)
        for col, txt, w in [("label", "名稱", 130), ("folder", "資料夾", 280),
                            ("cover", "封面", 100), ("rtp", "RTP", 100)]:
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
        ttk.Checkbutton(chk, text="強制更新 web player",
                        variable=self.refresh).pack(side="left", padx=4)

        self.run_btn = ttk.Button(f, text="重建並部署到網頁", command=self._run)
        self.run_btn.grid(row=5, column=0, sticky="w", pady=6)
        self.log = ScrolledText(f, width=78, height=14, state="disabled")
        self.log.grid(row=6, column=0, pady=6)

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for g in self.games:
            folder = str(g.get("folder") or "")
            folder_disp = folder if folder else "⚠ 待指定"
            cover = Path(g["cover"]).name if g.get("cover") else "（預設）"
            rtp = Path(g["rtp"]).name if g.get("rtp") else "（無）"
            self.tree.insert("", "end", values=(g.get("label") or "", folder_disp, cover, rtp))

    def _save(self):
        project.save_project(self.project_path, {
            "version": project.VERSION,
            "lib_name": self.lib_name.get(),
            "icon": self.icon.get(),
            "soundfont": self.soundfont.get(),
            "out": self.out.get(),
            "games": [
                {"folder": str(g.get("folder") or ""), "label": g.get("label") or "",
                 "cover": g.get("cover") or None, "rtp": g.get("rtp") or None}
                for g in self.games
            ],
        })

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.index(sel[0])

    def _add(self):
        dlg = GameDialog(self.root)
        self.root.wait_window(dlg)
        if dlg.result:
            self.games.append(dlg.result)
            self._refresh_tree()
            self._save()

    def _edit(self):
        i = self._selected_index()
        if i is None:
            return
        g = self.games[i]
        dlg = GameDialog(self.root, str(g.get("folder") or ""), g.get("label") or "",
                         g.get("cover") or "", g.get("rtp") or "")
        self.root.wait_window(dlg)
        if dlg.result:
            self.games[i] = dlg.result
            self._refresh_tree()
            self._save()

    def _remove(self):
        i = self._selected_index()
        if i is None:
            return
        name = self.games[i].get("label") or "這個遊戲"
        if not messagebox.askyesno(
                "移除遊戲",
                f"確定要從清單移除「{name}」嗎？\n（只移除清單，不會刪除遊戲原始資料夾）"):
            return
        del self.games[i]
        self._refresh_tree()
        self._save()

    def _move(self, delta):
        i = self._selected_index()
        if i is None:
            return
        j = i + delta
        if 0 <= j < len(self.games):
            self.games[i], self.games[j] = self.games[j], self.games[i]
            self._refresh_tree()
            self.tree.selection_set(self.tree.get_children()[j])
            self._save()

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
        if not self.games:
            messagebox.showerror("沒有遊戲", "請先用「＋ 加入遊戲」加至少一個遊戲")
            return
        missing = project.missing_sources(self.games)
        if missing:
            messagebox.showerror(
                "尚未指定原始資料夾",
                "以下遊戲還沒指定有效的原始資料夾（含 RPG_RT.ldb/.lmt），"
                "請先用「編輯」補上再部署：\n\n" + "\n".join("• " + m for m in missing))
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
                deploy=True,
                log=self._emit,
            )
            self._emit(f"✓ 完成並已部署，輸出在：{out}")
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

- [ ] **Step 4: 跑 GUI 測試確認通過**

Run: `python -m pytest tests/test_gui_smoke.py -v`
Expected: PASS（3 passed；若此環境無顯示則部分 skip，本機 Windows 應全 PASS）。

- [ ] **Step 5: 跑全部測試（不退步）**

Run: `python -m pytest -q`
Expected: 全部 PASS。

- [ ] **Step 6: Commit**

```bash
git add easyrpg_web_gui.py tests/test_gui_smoke.py
git commit -m "feat: GUI 持久化增刪查改＋一鍵重建並部署＋部署前安全閥"
```

---

### Task 5: `.gitignore` ＋ 一次性從線上產草稿 `library.json`

**Files:**
- Modify: `.gitignore`
- 產出（不進版控）: `library.json`

- [ ] **Step 1: 把 `library.json` 加入 `.gitignore`**

在 `.gitignore` 末尾新增一行：
```
library.json
```

- [ ] **Step 2: Commit `.gitignore`**

```bash
git add .gitignore
git commit -m "chore: gitignore library.json（含本機絕對路徑的使用者狀態）"
```

- [ ] **Step 3: 從線上 gh-pages 產草稿 `library.json`**

Run（在 repo 根目錄）：
```bash
cd /c/opensource/easyRPG-web
git fetch origin gh-pages
python -c "
import subprocess
import bootstrap, project, easyrpg_web_gui as gui
html = subprocess.check_output(['git', 'show', 'origin/gh-pages:index.html']).decode('utf-8')
draft = bootstrap.draft_project_from_menu(html)
project.save_project(gui.LIBRARY_JSON, draft)
print('wrote', gui.LIBRARY_JSON, '->', len(draft['games']), 'games')
"
```
Expected: 印出 `wrote …\library.json -> 6 games`。

- [ ] **Step 4: 驗證草稿內容**

Run:
```bash
python -c "
import project, easyrpg_web_gui as gui
proj, warn = project.load_project(gui.LIBRARY_JSON)
print('lib_name:', proj['lib_name'])
print('warning:', warn)
for g in proj['games']:
    print(repr(g['label']), 'folder=', repr(g['folder']))
"
```
Expected: `lib_name: RM作品收藏`、`warning: None`、6 個遊戲（月藍傳奇Ｉ、月藍傳奇ＩＩ、花嫁之冠、Education…、巴哈姆特、現在能感覺到風），且每個 `folder=''`（待使用者在 GUI 補回）。

- [ ] **Step 5: 確認 `library.json` 未被 git 追蹤**

Run: `git status --short`
Expected: 不出現 `library.json`（已被 ignore）；工作樹乾淨或僅未追蹤的建置產物。

---

## 自我審查結果（對照 spec）

- **Spec 覆蓋：** 專案檔載入/原子儲存（Task 1）；部署前安全閥 `missing_sources`（Task 2）；從線上 `index.html` 產草稿 `bootstrap.py`（Task 3）；GUI 查（載入）/增改刪（自動存檔，含 `GameDialog` 新增資料夾欄使草稿可補來源）/一鍵「重建並部署」`deploy=True`/Treeview「⚠ 待指定」/移除確認/部署前安全閥呼叫（Task 4）；`library.json` 進 `.gitignore` ＋ 一次性產草稿（Task 5）。build 核心不動。✔
- **Placeholder 掃描：** 無 TBD/TODO；每步含完整可執行碼與預期輸出。✔
- **型別/命名一致：** `project.default_project`/`load_project`(回 `(dict, warning)`)/`save_project`/`missing_sources`/`VERSION`、`bootstrap.draft_project_from_menu`、`App(root, project_path=None)`、`App._save`/`_refresh_tree`、`GameDialog(parent, folder="", label="", cover="", rtp="")` 全程一致。✔
- **任務間綠燈：** Task 1–3 純函式自帶測試；Task 4 改 GUI＋smoke 測試；Task 5 無 pytest 影響（僅 gitignore＋產檔）。每個任務結束 `python -m pytest -q` 全綠。✔
- **YAGNI：** 不做增量重建、不做多專案檔、不對 gh-pages 做差異 patch、不驗證 RTP。✔
