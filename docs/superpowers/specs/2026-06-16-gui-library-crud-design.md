# GUI 遊戲庫增刪查改（以遊戲專案為單位）＋一鍵部署 設計

**日期：** 2026-06-16
**分支：** `feat/gui-library-crud`
**專案根目錄：** `C:\opensource\easyRPG-web\`

## 目標

把目前無狀態的「每次從空清單重建」GUI，改成一個**持久化的遊戲庫編輯器**：以「遊戲專案」為單位，做到真正的增（Create）、查（Read）、改（Update）、刪（Delete），並能從 GUI **一鍵重建並部署**到線上網頁（GitHub Pages）。

非顯而易見的緣由：現有 `easyrpg_web_gui.py` 每次啟動 `self.games = []`，關窗即丟失全部狀態 → 沒有「查」現有庫、也沒有對既有庫的「改/刪」，只有「整包重建」。本設計補上持久層即可，**build 核心 `build_library` 完全不動**（沿用全量重建）。

## 決策（已與使用者確認）

| 項目 | 決策 |
| --- | --- |
| 狀態來源 | **專案檔**（`library.json`），與輸出 `dist/` 分離 |
| 專案檔管理 | **單一自動檔**：固定路徑、開窗自動載入、任何變動自動存檔（無手動 開啟/儲存 鈕） |
| 重建策略 | **每次全量重建**（依清單清空重生 `dist/`） |
| 部署 | **「重建並部署到網頁」單一主按鈕**：全量重建 → push 到 `gh-pages` |
| CRUD 單位 | **遊戲專案**（`library.json` 的 `games` 陣列每一筆＝一個遊戲專案） |

## 架構

### 新模組 `project.py`（純函式，與 Tkinter 隔離、可單測）

- `DEFAULT_PROJECT` — 預設專案 dict（空 `games`、預設 `lib_name/icon/soundfont/out`）。
- `load_project(path) -> tuple[dict, str | None]`
  - 回傳 `(project, warning)`。
  - 檔案不存在 → `(DEFAULT_PROJECT 複本, None)`。
  - JSON 損壞 / 結構不符 → `(DEFAULT_PROJECT 複本, "讀取 library.json 失敗：…（已以空庫開啟）")`。**永不丟例外**。
  - 載入時做欄位補齊（缺欄位用預設值填），確保回傳一定是完整 schema。
- `save_project(path, data) -> None`
  - UTF-8、`ensure_ascii=False`、`indent=2`。
  - **原子寫入**：寫到同目錄暫存檔再 `os.replace(tmp, path)`，避免寫到一半壞檔。

### `library.json` schema（單一自動檔）

固定路徑：應用程式目錄（`Path(__file__).resolve().parent / "library.json"`）。

```json
{
  "version": 1,
  "lib_name": "我的遊戲庫",
  "icon": "C:/opensource/easyRPG-web/assets/app_icon.png",
  "soundfont": "C:/opensource/easyRPG-web/assets/easyrpg.soundfont",
  "out": "dist",
  "games": [
    {"folder": "C:/games/Hanayome", "label": "花嫁之冠", "cover": null, "rtp": null}
  ]
}
```

- 路徑一律存成字串（絕對路徑）。`cover`/`rtp` 可為 `null`。
- `version` 供日後升級判斷。
- `deploy` / `refresh`（強制更新 player）為**每次執行的臨時開關，不持久化**（每次開窗預設關閉/沿用 UI 預設）。

## GUI 改動（`easyrpg_web_gui.py`）

### 查（Read）— 啟動即載入

- `App.__init__`：`proj, warning = project.load_project(LIBRARY_JSON)`（變數用 `proj`，別遮蔽模組名 `project`）；用 `proj` 還原 `lib_name / icon / soundfont / out` 與整份 `games`，立刻 `_refresh_tree()`。
- 若 `warning` 非 None，啟動後 `messagebox.showwarning` 提示一次，並以空庫繼續。
- 開窗即看得到目前庫裡有哪些遊戲專案（補上現缺的「查」）。

### 增 / 改 / 刪 — 每個動作自動存檔

沿用既有 Treeview ＋ 按鈕，於每個 mutation 結尾呼叫 `self._save()`：

- **增（Create）**：`_add` → `GameDialog` 回傳 → `append` → `_refresh_tree()` → `_save()`。
- **改（Update）**：
  - `_edit`（改名稱/封面/RTP）、`_move`（↑↓ 排序）→ mutation 後 `_save()`。
  - 上方欄位 `lib_name / icon / soundfont / out`：用 `StringVar.trace_add("write", …)` 綁定 `_save()`，欄位一變就存。
- **刪（Delete）**：`_remove` → 先 `messagebox.askyesno` 確認（防誤刪）→ `del` → `_refresh_tree()` → `_save()`。**只移除清單項，不刪遊戲原始資料夾**。

### `_save()` 實作

```python
def _save(self):
    project.save_project(LIBRARY_JSON, {
        "version": 1,
        "lib_name": self.lib_name.get(),
        "icon": self.icon.get(),
        "soundfont": self.soundfont.get(),
        "out": self.out.get(),
        "games": [
            {"folder": str(g["folder"]), "label": g["label"],
             "cover": g.get("cover"), "rtp": g.get("rtp")}
            for g in self.games
        ],
    })
```

trace 綁定須在初次載入欄位值**之後**再掛上，避免初始化時誤觸發寫檔（或 `_save` 本身無害，重複寫同內容也可接受——以實作簡潔為準）。

### 一鍵部署

- 主按鈕文字：`開始打包遊戲庫` → **`重建並部署到網頁`**。
- 移除「完成後部署到 GitHub Pages」勾選框（折進主按鈕）；**保留**「強制更新 web player」勾選框。
- `_worker` 呼叫 `core.build_library(..., deploy=True, refresh_player=self.refresh.get())`——`build_library` 已內建 `deploy=True` → `deploy.deploy_gh_pages`，無需改核心。
- 沿用既有背景執行緒 + log 佇列：`git` 指令與成功/失敗即時顯示在 log 區；任何錯誤（無 remote、認證失敗等）由 `_worker` 的 `except` 捕捉並回報、按鈕復原，不崩潰。

## 錯誤處理

- 缺檔 → 空庫開啟；壞檔 → 警告一次後空庫開啟。
- 寫檔原子化（temp + `os.replace`）。
- 重建/部署在背景執行緒，例外一律進 log 區、按鈕狀態復原。
- 空清單按重建：沿用現有 `messagebox.showerror`（`build_library` 亦會丟 `BuildError`）。

## 測試

- `tests/test_project.py`（新增，純函式）：
  - `load_project` 缺檔 → 回 default、warning 為 None。
  - `load_project` 壞 JSON → 回 default、warning 非 None（不丟例外）。
  - `load_project` 缺欄位 → 補齊為完整 schema。
  - round-trip：`save_project` 後 `load_project` 還原相同內容（含中文不被跳脫成 \uXXXX、含 `null` 的 cover/rtp）。
  - 原子寫入：`save_project` 寫到既有檔不會留下暫存檔。
- `tests/test_gui_smoke.py`（沿用既有風格擴充）：建立 `App`（指向 tmp 的 `library.json`）→ 模擬 add/remove → 斷言 `library.json` 內容；啟動時讀既有 `library.json` → 斷言 Treeview 列數正確。GUI 測試需可注入 `LIBRARY_JSON` 路徑（例如 `App(root, project_path=...)` 參數，預設用模組常數）。

## 不做（YAGNI）

- 不做增量重建（已決定全量）。
- 不做多專案檔 開啟/儲存/另存（已決定單一自動檔）。
- 不對線上 gh-pages 做差異 patch（全量 force-push 沿用 `deploy.py`）。
- 不驗證 RTP（沿用既有原則：純由使用者勾選決定）。
```
