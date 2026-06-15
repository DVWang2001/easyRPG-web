# easyRPG-web 多遊戲庫（Library）+ 圖示網格選單，GUI 驅動

- 狀態：已通過設計討論（brainstorming），待寫實作計畫
- 日期：2026-06-15
- 專案：`C:\opensource\easyRPG-web\`（延伸既有 easyRPG-web 工具，分支 `feat/multi-game-library`）
- 前置：建立在已實作的單一遊戲工具之上（PR #1 / `feat/easyrpg-web-impl`）

## 背景與目標

現有 easyRPG-web 只能把**一個**遊戲打包成 `games/default/` 自動啟動的 PWA。使用者想「載入很多種遊戲」，並且**要能用 GUI 做到**。

EasyRPG 網頁版原生支援多遊戲：每個遊戲放 `games/<名字>/`（各自一份 `index.json`），用 `?game=<名字>` 切換。本功能在此之上，產出**一個**自包含網站：打開先看到**圖示網格的「遊戲庫選單」**，點任一遊戲進去玩。

**目標**
- 一次打包多個 RPG Maker 遊戲成單一 PWA 遊戲庫，部署一次、一個主畫面圖示。
- App 開啟即見**圖示網格**選單（每遊戲一個封面圖 + 名稱）。
- 全程可用 **GUI**（清單編輯器）完成：加入/移除/排序遊戲、各自設名稱與封面。
- 沿用既有賣點：Windows 音色 SF2、離線 PWA、純 Windows、不需編譯。

**非目標**
- 不做原生 .ipa、不自行編譯 player。
- 不做每遊戲各自音色/RTP（YAGNI；音色全庫共用一個）。
- 不取代既有單一遊戲 `build()`（保留）。

## 整體架構

產出 `dist/`：
```
dist/
├─ index.html          ← 【新】圖示網格「遊戲庫選單」（App 一開看到的）
├─ play.html           ← EasyRPG 官方 player（原本的 index.html 改名）
├─ index.js / index.wasm
├─ icons/icon.png      ← 整個遊戲庫的主圖示（PWA home-screen icon）
├─ games/
│   ├─ <slugA>/  (index.json + 遊戲檔 + 共用 easyrpg.soundfont + cover.png)
│   ├─ <slugB>/  …
│   └─ <slugC>/  …
├─ manifest.webmanifest  (start_url = "." → 網格選單)
└─ service-worker.js     (precache 整個 dist：全部遊戲 + player + 封面 + 選單)
```
點網格中的遊戲 → 開 `play.html?game=<slug>` → 載入該遊戲。

**為什麼選單當 `index.html`、player 改名 `play.html`：** 「一打開就是遊戲庫」最直覺，PWA `start_url` 指選單即可。EasyRPG player 靠網址 `?game=` 參數運作（讀 query string，與 HTML 檔名無關），改名不影響其載入 `index.js`/`index.wasm`。

## 元件

| 檔案 | 變更 | 角色 | 依賴 |
|---|---|---|---|
| `slugify.py` | 新增 | 遊戲名/夾名 → 安全且唯一的 slug（網址與資料夾用） | 標準庫 |
| `menu.py` | 新增 | 產生圖示網格 `index.html`（純 HTML/CSS、無框架）；每格＝封面圖+名稱→連 `play.html?game=<slug>`；標題與名稱做 HTML 跳脫 | 標準庫 |
| `library.py` | 新增 | 收多個遊戲規格 → 各自 staging 到 `games/<slug>/`、各自 gencache、注入共用 SF2 與每遊戲封面 `cover.png`；非法遊戲中止並指名 | 既有 `staging`/`gencache` |
| `easyrpg_web_build.py` | 加入口 | 新增 `build_library(games, app_label, app_icon, soundfont, out, ignore, refresh_player, deploy, player_cache, player_url, log)`；player 取回後將 `index.html`→`play.html`；呼叫 library + menu + pwa；舊 `build()` 保留 | 既有模組 |
| `pwa.py` | 微調 | `write_service_worker` 已掃描整個 `dist/`（含 play.html、games、封面、選單），免改；`write_manifest` start_url 維持 `"."`（現已是）；`patch_index_html` 改為作用在 `play.html`（注入 SW 註冊與 apple meta），選單 `index.html` 由 `menu.py` 自帶這些標籤 | — |
| `easyrpg_web_gui.py` | 改寫成清單編輯器 | 多遊戲列表 + 全庫設定；呼叫 `build_library`；沿用 threading/queue 即時 log | Tkinter |

### 資料結構
一個「遊戲規格」是 dict：`{"folder": <path>, "label": <str>, "cover": <path|None>, "slug": <str>}`（slug 由 `build_library` 在驗證後填入，確保唯一）。

## GUI（重點）

單一視窗，上半遊戲清單、下半全庫設定 + 打包：
```
┌ 遊戲庫名稱: [我的遊戲庫        ]   App圖示:[…預設…][選]
├ 遊戲清單 ────────────────────────────────────┐
│  名稱          資料夾                  封面      │
│  花嫁之冠   C:\Games\Hanayome     cover1.png   │
│  勇者傳說   C:\Games\Brave        (預設)       │
│  …                                             │
│  [ + 加入遊戲 ] [ 編輯 ] [ 移除 ] [ ↑ ] [ ↓ ]  │
└────────────────────────────────────────────────┘
  音色SF2:[…預設 Windows 音色…][選]    輸出夾:[dist]
  ☐ 完成後部署到 GitHub Pages    ☐ 強制更新 player
  [ 開始打包遊戲庫 ]
  ┌ log ─────────────────────────────────────────┐
```
- 清單用 `ttk.Treeview`（欄：名稱 / 資料夾 / 封面）。
- **「+ 加入遊戲」**：選遊戲資料夾 → 彈小對話框填「顯示名稱（預設＝夾名）」與「封面圖（選填，可留空）」→ 加進清單。
- **編輯**：改選定列的名稱/封面。**移除**：刪選定列。**↑ / ↓**：調整順序（＝網格顯示順序）。
- 全庫設定：遊戲庫名稱（→ manifest name 與選單標題）、App 圖示、共用音色 SF2、輸出夾、部署/更新勾選。
- **「開始打包遊戲庫」**：背景執行緒跑 `build_library(games=清單, ...)`，即時 log；完成跳訊息與輸出路徑。
- 至少要一個遊戲才可打包（否則提示）。

## 資料流 / 邊界處理

- **slug 規則**：取 label（無則夾名）→ Unicode 正規化、轉小寫、空白→`-`、移除 `/\:*?"<>|` 等不安全字元、壓多餘 `-`；空結果退回 `game`；與既有 slug 衝突時加 `-2`、`-3`…。中文允許保留（網址用 percent-encode，檔名 Windows/Pages 支援 UTF-8）。
- **非法遊戲**：每個遊戲跑 `_validate_game`（缺 `RPG_RT.ldb/.lmt`）。**任一不合法 → 中止整個打包**，log/例外明確指出是「哪個遊戲（label + 路徑）」缺什麼。（使用者選定：不靜默略過。）
- **封面選填**：未提供 → 該格用 App 主圖示 `icons/icon.png` 當縮圖（menu.py 以同一相對路徑引用，不另存 cover）。
- **空清單**：`build_library` 拒絕（至少一個遊戲）。
- **CLI 範圍（v1）**：遊戲庫的主要入口是 **GUI**；`build_library` 同時是可被測試/呼叫的 Python 函式。本版**不新增**多遊戲的命令列旗標（多遊戲清單用 GUI 維護即可），既有單一遊戲 CLI `build` 維持不變。
- **player 改名**：取回 player 後，在 `dist/` 內把 `index.html` 重新命名為 `play.html` 再對其 `patch_index_html`；接著 `menu.py` 寫入新的 `index.html`（選單）。順序確保 SW（最後寫）precache 到兩個 html。

## 測試策略

- **`slugify`**：重複名 → `x`,`x-2`,`x-3`；中文/特殊字元/空字串 → 安全非空 slug；純函式單元測試。
- **`menu.py`**：給 N 個遊戲規格 → `index.html` 含 N 個 `href="play.html?game=<slug>"`、每格 `<img>` 指向正確封面、標題與名稱經 HTML 跳脫、含 manifest/apple-touch/SW 註冊標籤。
- **`library.py`**：兩個假遊戲 → `games/<slugA>`、`games/<slugB>` 各有 `index.json` + `easyrpg.soundfont` + `cover.png`（或封面缺時不產 cover）；slug 唯一；非法遊戲 → 拋明確錯誤含 label。
- **端對端 `build_library`**（假 player tarball）：兩遊戲 → `dist/index.html`(網格含兩連結)、`dist/play.html`(原 player + PWA 標籤)、`games/<slugA|B>/index.json`、`manifest.webmanifest`(start_url ".")、`service-worker.js` precache 同時含 `play.html` 與兩遊戲資產。
- **GUI 煙霧測試**：`easyrpg_web_gui.py` 可匯入、有 `App`、且 build 動作走 `core.build_library`（不重複邏輯）。
- **真實端對端（人工/驗證任務）**：用兩個真實遊戲打包 → `http.server` 起 `dist/` → 瀏覽器確認網格選單出現、點圖示進入正確遊戲。

## 與既有程式的關係

- 同一個 `easyRPG-web` 專案/repo，新分支 `feat/multi-game-library`。
- 重用既有 `staging`/`gencache`/`player_fetch`/`pwa` 模組（呼叫，不複製）。
- 既有單一遊戲 `build()` 與其 CLI 參數保留；`easyrpg_web_gui.py` 從單一遊戲改寫為遊戲庫清單編輯器（GUI 主流程改為多遊戲；單一遊戲仍可由 CLI `build` 或加一個遊戲的庫達成）。
- 沿用編碼規則：中文 `.bat` UTF-8 BOM、`.sh` LF no-BOM。
