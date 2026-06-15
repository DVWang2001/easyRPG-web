# 每遊戲可選 RTP（使用者勾選）

- 狀態：已通過設計討論，待寫實作計畫
- 日期：2026-06-15
- 專案：`C:\opensource\easyRPG-web\`（分支 `feat/per-game-rtp`，堆疊在多遊戲庫 `feat/multi-game-library` / PR #2 之上）

## 背景與目標

多遊戲庫目前每個遊戲只設名稱與封面。有些 RPG Maker 遊戲缺素材，需要先灌入 RTP（Run-Time Package）。RPG Maker 2000 與 2003 的 RTP 不同，遊戲庫可能混用，故 **RTP 以每個遊戲各自選資料夾** 處理。

既有 `staging.stage_game(..., rtp=...)` 已支援 RTP（先鋪 RTP，再用遊戲檔覆蓋同名素材）；多遊戲路徑只是還沒接通。

**目標**：在每個遊戲的設定對話框，讓使用者**自己勾選是否加入 RTP** 並選 RTP 資料夾；勾了就把該資料夾接給既有 staging。

**重要原則**：**程式不判斷、不驗證、不中止**。是否加入 RTP 完全由使用者勾選決定；RTP 路徑空或內容不對，程式不報錯、不擋（責任在使用者）。

**非目標**：自動偵測遊戲版本配對 RTP、全庫共用 RTP 池、RTP 合法性驗證。

## 設計

### 資料模型
每個遊戲規格 dict 多一個選填鍵 `"rtp": <資料夾路徑> | None`。
- 僅當使用者「勾選加入 RTP」且選了資料夾時，`rtp` 才帶值；否則為 `None`。

### 1. GUI `GameDialog`（`easyrpg_web_gui.py`）
在「封面圖」列之後新增：
- 一個勾選框 **「加入 RTP」**（`tk.BooleanVar`）。
- 一列 **「RTP 資料夾」**：Entry + 「…」按鈕（按鈕用 `filedialog.askdirectory` 選**資料夾**）。
- 送出（確定）時：`rtp = v_rtp.get().strip() if v_rtp_enabled.get() else None`，放進 result dict 的 `"rtp"`。
- 編輯既有遊戲時，依其 `rtp` 預填（有值則勾選並填路徑）。

### 2. GUI 清單 `Treeview`
新增一欄 **「RTP」**，顯示 RTP 資料夾名稱（`Path(rtp).name`）或「（無）」。欄位順序：名稱 / 資料夾 / 封面 / RTP。

### 3. `library.stage_library`（`library.py`）
把每個遊戲的 `rtp` 接給既有 staging：
```python
staging.stage_game(g["folder"], dest, ignore_globs=ignore_globs,
                   soundfont=soundfont, rtp=g.get("rtp"))
```
其餘不變（`stage_game` 先鋪 RTP、遊戲覆蓋）。

### 4. `build_library`（`easyrpg_web_build.py`）
`specs = [dict(g) for g in games]` 已會保留 `rtp` 鍵，傳到 `library.stage_library` 即可。**不新增任何 RTP 驗證**（呼應「程式不判斷」）。`rtp` 預設 `None`（既有呼叫者不帶 `rtp` 時行為不變）。

## 邊界處理
- 沒勾選 / `rtp=None`：與現狀完全相同，不灌 RTP。
- 勾了但路徑空或不存在：`staging._copy_tree(Path(rtp))` 以 `rglob` 走訪，找不到就自然不複製任何東西，**不報錯**（符合「不判斷」）。
- 多遊戲各自獨立：A 遊戲的 RTP 不影響 B 遊戲（各自 `stage_game`）。

## 測試
- `tests/test_library.py`：新增一案 —— 某遊戲帶 `rtp`（一個含 `shared.png` 與同名於遊戲的 `RPG_RT.ldb` 的假 RTP 夾）→ `games/<slug>/shared.png` 來自 RTP、`RPG_RT.ldb` 為遊戲版本（遊戲覆蓋 RTP）。
- `tests/test_build_library.py`：新增一案 —— games 內某遊戲帶 `rtp` → 該遊戲 `games/<slug>/` 出現 RTP 專屬檔。
- 不新增「非法 RTP 報錯」測試（已決定不判斷）。
- `tests/test_gui_smoke.py`：維持（import 煙霧）；RTP 接通由上述兩測試涵蓋。

## 與既有程式的關係
- 同 `easyRPG-web` 專案。重用 `staging.stage_game` 的 rtp 能力（呼叫，不改其邏輯）。
- 只動 `library.py`（接通）、`easyrpg_web_gui.py`（對話框 + 欄位）；`build_library` 因 `dict(g)` 已自動帶過 `rtp`，最小或零改動。
- 沿用編碼規則：中文 `.bat` UTF-8 BOM、`.sh` LF no-BOM（本次不動這些檔）。
