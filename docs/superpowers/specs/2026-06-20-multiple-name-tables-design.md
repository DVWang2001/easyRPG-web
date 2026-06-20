# 設計：多個自訂取名字表

日期：2026-06-20

## 背景與目標

目前 EasyRPG-web 只支援**單一全域**自訂取名字表：`library.json` 裡有一個
`name_table = {zh_tw_1, zh_tw_2}`（漢一/漢二兩頁），每個遊戲只有一個
`custom_player` 布林旗標決定是否使用它。所有勾選的遊戲共用同一份字表。

問題：每套字表只有 ~172 格（漢一 86 + 漢二 86），不同遊戲的角色名字用字不同，
現在所有自訂遊戲被迫共用同一份字。

**目標**：支援多個具名字表，每個遊戲從清單中挑一個使用（沒挑＝官方播放器）。

## 使用者決策（brainstorming 結論）

1. **字表↔遊戲關係**：每遊戲從一份具名字表清單裡挑一個（沒挑＝官方版）。
2. **重建模式**：每個字表各自重建、各自快取；只重編改過的，編過的略過。
3. **字表識別**：使用者取中文名，程式自動配 id（沿用既有 `slugify.hash_slug`）。

## 資料模型（project.py / library.json）

把單一 `name_table` 物件改成 `name_tables` 清單；遊戲的 `custom_player` 布林改成
`name_table_id` 字串參照。

```jsonc
// 專案層級
"name_tables": [
  { "id": "a1b2c3d4e5f6a7b8", "name": "仙劍奇俠字表", "zh_tw_1": "...", "zh_tw_2": "..." },
  { "id": "d4e5f6a7b8c9d0e1", "name": "RPG通用字表",  "zh_tw_1": "...", "zh_tw_2": "..." }
]

// 每個遊戲
"name_table_id": "a1b2c3d4e5f6a7b8"   // 空字串/缺欄位/null = 用官方播放器
```

### id 產生（建立時一次，之後固定）

- 新增字表時用 `slugify.hash_slug(name, taken)` 產生 id（名稱 NFKC 正規化後 sha256
  前 16 碼，同名碰撞加 `-2`/`-3`），檔名安全、與遊戲網址雜湊一致。
- **id 建立後固定不變**：之後改名只改 `name`，不動 id。如此遊戲的 `name_table_id`
  參照與 `players/custom/<id>/` 快取都不必跟著搬移，避免一連串同步更新。
  （`taken` 帶入既有 id 集合避免碰撞。）

### 向後相容遷移（`_normalize`）

載入舊檔（含 `name_table` 物件、遊戲含 `custom_player` 布林）時：

- 若舊 `name_table` 任一頁非空 → 轉成 `name_tables` 清單第一筆，名稱預設「自訂字表」，
  id 由該名稱 hash_slug 產生。若兩頁皆空且無遊戲勾選 → `name_tables` 為空清單。
- 遊戲 `custom_player: true` → `name_table_id` 指向上述遷移字表的 id；
  `custom_player: false`/缺 → `name_table_id` 空字串。
- 已是新格式（有 `name_tables`）的檔案：正規化每筆字表（id/name/zh_tw_1/zh_tw_2），
  丟棄參照到不存在 id 的遊戲 `name_table_id`（設回空字串）。

每個字表仍保留漢一/漢二兩頁結構——這是 EasyRPG Player 鍵盤本身的版面限制，不改。

## 建置快取（customplayer.py / players/custom/）

每個字表編出的引擎各自快取在以 id 命名的子資料夾：

```
players/custom/<id>/index.html
players/custom/<id>/index.js
players/custom/<id>/index.wasm
players/custom/<id>/source.json    ← {"zh_tw_1": "...", "zh_tw_2": "..."}（編譯當下的來源）
```

- `rebuild_custom_player` 改成接受 `(table_id, zh_tw_1, zh_tw_2, log)`，輸出到
  `players/custom/<id>/`，並寫入 `source.json`。
- **過期判斷**：新增純函式（例如 `customplayer.is_stale(table)` 或在 GUI 比對）讀取
  `players/custom/<id>/source.json`，與字表目前的 `zh_tw_1/zh_tw_2` 比對；不一致或檔案
  不存在 → 過期/未編。GUI 用此標示。
- 沿用既有 Docker 流程（注入 window_keyboard.cpp → 容器重編 → 取出 index.*）。

## 打包到 dist（easyrpg_web_build.py / library.py / pwa.py）

- `library.stage_library` 產出的 entry：把 `custom`（布林）改成帶 `name_table_id`
  （或沿用一個欄位帶 id；空＝官方）。
- 建置時掃描所有遊戲用到的 `name_table_id`（去重、忽略空值），每個從
  `players/custom/<id>/` 複製 `index.js`/`index.wasm` 到 `dist/player-custom-<id>/`。
- 若某個被用到的字表在 `players/custom/<id>/` 找不到引擎 → 丟 `BuildError`，
  訊息指名是哪個字表（顯示名稱），提示去 GUI 重建。
- `pwa.write_game_pages`：每個遊戲依自己的 `name_table_id` 決定引擎路徑
  `player-custom-<id>/`；無 id → 用根目錄官方引擎（`engine = ""`）。

## GUI（easyrpg_web_gui.py）

### 字表管理

原本「編輯取名字表…」單一對話框 → **字表管理清單對話框**：

- 列出所有字表（名稱 + 過期/已編狀態）。
- 動作：新增字表、改名、刪除、編輯字格（漢一/漢二，沿用現有兩個文字框 UI）、
  重建該字表（呼叫 `customplayer.rebuild_custom_player`，需 Docker 環境）。
- **改名**：只改 `name`，id 不變；遊戲參照與快取資料夾都不受影響。
- **刪除**：把指向它的遊戲 `name_table_id` 設回空字串（可選：一併刪除
  `players/custom/<id>/` 快取資料夾）。

### 遊戲設定對話框

- 「使用自訂取名字表（自建播放器）」核取方塊 → **下拉選單**：選項為「（無）」＋各字表名稱。
  選中值對應 `name_table_id`。
- 主視窗遊戲表格「自訂字表」欄：顯示**字表名稱**（而非打勾），無則空白。

## 受影響檔案

- `project.py` — schema、`_normalize` 遷移、`default_project`。
- `customplayer.py` — `rebuild_custom_player` 帶 id、寫 source.json、過期判斷。
- `easyrpg_web_build.py` — 多字表引擎複製、缺引擎報錯指名。
- `library.py` — entry 帶 name_table_id。
- `pwa.py` — `write_game_pages` 依 id 選引擎。
- `easyrpg_web_gui.py` — 字表管理清單、遊戲下拉、表格欄。
- `nametable.py` — **不變**（仍是 render(template, zh_tw_1, zh_tw_2)）。
- 測試：`test_project.py`、`test_customplayer.py`、`test_build_library.py`、
  `test_library.py`、`test_gui_smoke.py` 對應更新；新增多字表案例。

## 非目標（YAGNI）

- 不改 Player 鍵盤的兩頁版面（漢一/漢二）。
- 不做字表匯入/匯出、字表間複製字格等進階管理。
- 不做自動偵測遊戲所需用字。
