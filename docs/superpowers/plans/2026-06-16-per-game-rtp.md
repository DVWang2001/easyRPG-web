# 每遊戲可選 RTP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓多遊戲庫的每個遊戲，由使用者在「遊戲設定」對話框勾選是否加入 RTP 並選 RTP 資料夾；勾了就把該資料夾接給既有 staging（程式不判斷、不驗證）。

**Architecture:** `staging.stage_game(..., rtp=)` 既有能力（先鋪 RTP、遊戲覆蓋）已存在；本計畫只把 `rtp` 接通 `library.stage_library`，並在 `easyrpg_web_gui.py` 的 `GameDialog` 加「加入 RTP」勾選框 + RTP 資料夾欄、Treeview 加 RTP 欄。`build_library` 因 `specs=[dict(g) for g in games]` 已自動帶過 `rtp`，零改動。

**Tech Stack:** Python 3.8+（標準庫 + tkinter）；pytest。

**Spec:** `docs/superpowers/specs/2026-06-15-per-game-rtp-design.md`
**專案根目錄：** `C:\opensource\easyRPG-web\`（分支 `feat/per-game-rtp`）

---

## 檔案結構

| 檔案 | 變更 | 職責 |
|---|---|---|
| `library.py` | 修改 | `stage_game` 呼叫加 `rtp=g.get("rtp")` |
| `easyrpg_web_gui.py` | 整檔重寫 | `GameDialog` 加「加入 RTP」勾選框 + RTP 資料夾欄；`App` Treeview 加 RTP 欄、編輯時預填 rtp |
| `tests/test_library.py` | 加測試 | 帶 rtp → RTP 檔進遊戲夾、遊戲覆蓋 RTP |
| `tests/test_build_library.py` | 加測試 | 端對端：某遊戲帶 rtp → RTP 檔進 `games/<slug>/` |

---

### Task 1: 把 RTP 接通 `library.stage_library`（含端對端）

**Files:**
- Modify: `library.py`
- Test: `tests/test_library.py`（新增一案）、`tests/test_build_library.py`（新增一案）

- [ ] **Step 1: 在 `tests/test_library.py` 末尾新增失敗測試**

```python
def test_stage_library_with_rtp(tmp_path):
    out = tmp_path / "dist"
    g1 = tmp_path / "g1"
    g1.mkdir()
    (g1 / "RPG_RT.ldb").write_text("game-version")
    rtp = tmp_path / "rtp"
    rtp.mkdir()
    (rtp / "shared.png").write_text("from-rtp")
    (rtp / "RPG_RT.ldb").write_text("rtp-version")
    games = [{"folder": g1, "label": "G", "slug": "g", "cover": None, "rtp": rtp}]

    library.stage_library(out, games, soundfont=None)

    # RTP 補進來的素材
    assert (out / "games" / "g" / "shared.png").read_text() == "from-rtp"
    # 遊戲自有檔覆蓋 RTP 同名檔
    assert (out / "games" / "g" / "RPG_RT.ldb").read_text() == "game-version"
```

- [ ] **Step 2: 在 `tests/test_build_library.py` 末尾新增失敗測試**

（此檔頂部已有 `_fake_player_tarball` 與 `_game` 輔助函式，沿用。）
```python
def test_build_library_passes_rtp_through(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    g1 = tmp_path / "Game"
    _game(g1, "1")
    rtp = tmp_path / "rtp"
    rtp.mkdir()
    (rtp / "extra.png").write_text("rtp-asset")
    out = tmp_path / "dist"

    core.build_library(
        games=[{"folder": g1, "label": "遊戲", "cover": None, "rtp": rtp}],
        app_icon=None, soundfont=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )

    assert (out / "games" / "遊戲" / "extra.png").read_text() == "rtp-asset"
```

- [ ] **Step 3: 跑兩個新測試確認失敗**

Run: `python -m pytest tests/test_library.py::test_stage_library_with_rtp tests/test_build_library.py::test_build_library_passes_rtp_through -v`
Expected: 兩個都 FAIL（RTP 未接通 → `shared.png`/`extra.png` 不存在）。

- [ ] **Step 4: 修改 `library.py` 接通 rtp**

把現有 `stage_library` 中的這行：
```python
        staging.stage_game(g["folder"], dest, ignore_globs=ignore_globs, soundfont=soundfont)
```
改成：
```python
        staging.stage_game(g["folder"], dest, ignore_globs=ignore_globs,
                           soundfont=soundfont, rtp=g.get("rtp"))
```

- [ ] **Step 5: 跑兩個新測試確認通過**

Run: `python -m pytest tests/test_library.py::test_stage_library_with_rtp tests/test_build_library.py::test_build_library_passes_rtp_through -v`
Expected: 兩個都 PASS。

- [ ] **Step 6: 跑全部測試確認沒退步**

Run: `python -m pytest -q`
Expected: 全部 PASS（原 36 + 新 2 = 38）。

- [ ] **Step 7: Commit**

```bash
git add library.py tests/test_library.py tests/test_build_library.py
git commit -m "feat: 多遊戲庫把每遊戲 RTP 接通 staging"
```

---

### Task 2: GUI —— `GameDialog` 加「加入 RTP」勾選 + RTP 欄

**Files:**
- Modify（整檔重寫）: `easyrpg_web_gui.py`

> 此任務無法用單元測試驗證對話框互動（Tkinter 需開視窗）；以「整檔重寫 + import 煙霧測試保持綠燈 + 手動開窗確認」驗收。RTP 真正接通的行為已由 Task 1 的測試涵蓋。

- [ ] **Step 1: 確認既有 smoke 測試仍綠（基準）**

Run: `python -m pytest tests/test_gui_smoke.py -q`
Expected: PASS（沿用現有 `tests/test_gui_smoke.py`，本任務不改它）。

- [ ] **Step 2: 整檔重寫 `easyrpg_web_gui.py` 為以下內容**

（相對現狀的差異：`GameDialog` 增加 `rtp` 參數、`v_rtp_on` 勾選與 `v_rtp` 路徑列與 `_pick_rtp`，`_ok` 產出 `rtp`；`App` 的 Treeview 多一欄 `rtp`、`_refresh_tree` 顯示 RTP、`_edit` 預填 rtp。）

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
    """加入/編輯單一遊戲：名稱 + 封面（選填）+ RTP（勾選＋資料夾）。回傳 dict 或 None。"""

    def __init__(self, parent, folder, label="", cover="", rtp=""):
        super().__init__(parent)
        self.title("遊戲設定")
        self.result = None
        self.transient(parent)
        self.grab_set()

        self.v_label = tk.StringVar(value=label or Path(folder).name)
        self.v_cover = tk.StringVar(value=cover)
        self.v_rtp_on = tk.BooleanVar(value=bool(rtp))
        self.v_rtp = tk.StringVar(value=rtp)

        ttk.Label(self, text=f"資料夾：{folder}").grid(row=0, column=0, columnspan=3,
                                                     sticky="w", padx=8, pady=6)
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

        self._folder = folder

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
        if not self.v_label.get().strip():
            messagebox.showerror("缺少名稱", "請輸入顯示名稱", parent=self)
            return
        rtp = self.v_rtp.get().strip() if self.v_rtp_on.get() else ""
        self.result = {
            "folder": self._folder,
            "label": self.v_label.get().strip(),
            "cover": self.v_cover.get().strip() or None,
            "rtp": rtp or None,
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
        ttk.Checkbutton(chk, text="完成後部署到 GitHub Pages",
                        variable=self.deploy).pack(side="left", padx=4)
        ttk.Checkbutton(chk, text="強制更新 web player",
                        variable=self.refresh).pack(side="left", padx=4)

        self.run_btn = ttk.Button(f, text="開始打包遊戲庫", command=self._run)
        self.run_btn.grid(row=5, column=0, sticky="w", pady=6)
        self.log = ScrolledText(f, width=78, height=14, state="disabled")
        self.log.grid(row=6, column=0, pady=6)

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for g in self.games:
            cover = Path(g["cover"]).name if g.get("cover") else "（預設）"
            rtp = Path(g["rtp"]).name if g.get("rtp") else "（無）"
            self.tree.insert("", "end", values=(g["label"], str(g["folder"]), cover, rtp))

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
        dlg = GameDialog(self.root, g["folder"], g["label"],
                         g.get("cover") or "", g.get("rtp") or "")
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

- [ ] **Step 3: 跑全部測試**

Run: `python -m pytest -q`
Expected: 全部 PASS（仍 38）。

- [ ] **Step 4: 匯入煙霧檢查（不開窗）**

Run: `python -c "import easyrpg_web_gui as g; print(hasattr(g,'GameDialog'), hasattr(g,'App'))"`
Expected: `True True`

- [ ] **Step 5: 手動開窗確認（建議）**

Run: `python easyrpg_web_gui.py`
Expected: 「＋ 加入遊戲」→ 對話框可見「加入 RTP」勾選框與「RTP 資料夾」選夾按鈕；勾選並選資料夾後，清單 RTP 欄顯示該資料夾名；不勾顯示「（無）」。關閉即可。

- [ ] **Step 6: Commit**

```bash
git add easyrpg_web_gui.py
git commit -m "feat: GameDialog 加「加入 RTP」勾選與資料夾欄、清單顯示 RTP"
```

---

## 自我審查結果（對照 spec）

- **Spec 覆蓋：** 每遊戲 `rtp` 鍵（Task 1 測試資料）、`library` 接通（Task 1 Step 4）、`build_library` 零改動帶過（Task 1 Step 2 端對端測試）、GUI 勾選框 + RTP 資料夾欄 + 編輯預填（Task 2 GameDialog）、Treeview RTP 欄（Task 2 `_refresh_tree`/欄定義）、不判斷不驗證（無任何 RTP 驗證碼）。✔
- **Placeholder 掃描：** 無 TBD/TODO；每段含完整可執行碼與預期輸出。Task 2 已說明為何用「重寫 + 煙霧 + 手動」而非單元測試（Tkinter 互動）。✔
- **型別/簽章一致性：** 遊戲規格 dict 鍵 `{folder,label,slug,cover,rtp}`；`stage_game(..., rtp=)`、`stage_library` 內 `g.get("rtp")`、`GameDialog(parent, folder, label, cover, rtp)`、`_ok` 產出含 `rtp` 在各處一致。✔
- **既有行為不變：** 不帶 `rtp`（既有測試與單一遊戲路徑）→ `g.get("rtp")` 回 `None` → `stage_game(rtp=None)`（與現狀相同）。✔
