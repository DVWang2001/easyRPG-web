# 每遊戲各自一個靜態播放頁（讓 iOS 也能換 icon）

- 狀態：已通過設計討論，待寫實作計畫
- 日期：2026-06-16
- 專案：`C:\opensource\easyRPG-web\`（分支 `feat/per-game-play-pages`）

## 背景與目標

前一版用 JS 在 `play.html` 載入後動態換 favicon/title。實機驗證：**桌機 icon 會變、iOS Safari 不會**（iOS 在解析 HTML 時就決定 favicon，忽略 JS 後注入）。標題在兩端都可變，但 icon 在 iPhone 上維持舊圖。

**目標：讓 iPhone 上點進遊戲後，分頁 icon 也變成該遊戲封面。** 唯一可靠做法：把 icon 與 title **靜態寫在每個遊戲自己的 HTML `<head>`**。因為目前所有遊戲共用一個 `play.html`，故改為**每遊戲產生一個 `play-<slug>.html`**。

**非目標**
- 每遊戲各自的「加入主畫面」PWA 圖示（整個庫仍是單一 PWA，home-screen 圖示是庫主圖示）。
- 改 `library.py`、改單一遊戲 `build()`。

## 架構 / 做法

對每個遊戲，以既有 `play.html`（patch 過的 EasyRPG player）為**模板**，產生 `dist/play-<slug>.html`：
- 靜態 `<title>遊戲名</title>`（取代模板原本的 `<title>`）。
- 靜態 `<link rel="icon" href="games/<slug>/cover.png">` 與 `<link rel="apple-touch-icon" href=...>`（沒封面則用庫主圖示 `icons/icon.png`）。
- 把 player 設定 `createEasyRpgPlayer({ game: undefined … })` 改寫成 `({ game: '<slug>' … })`，遊戲 baked-in，**不再需要 `?game=`**。

放在根目錄（與 `play.html` 同層），故 `index.js`/`index.wasm`/`games/<slug>/` 的相對路徑與原本完全一致。

**為什麼解 iOS：** icon 靜態寫在 head，頁面一解析就在 → iOS Safari 會採用 → 手機分頁小圖會變。

## 元件 / 改動（只動 easyRPG-web）

| 檔案 | 變更 | 說明 |
|---|---|---|
| `pwa.py` | **新增** `write_game_pages(dist, entries, icon_rel=ICON_REL)` | 讀 `dist/play.html` 當模板；對每個 entry 產出 `dist/play-<slug>.html`（換 title、注入 icon 連結、baked-in game）。**移除** `inject_play_game_info`（被靜態頁取代，且 iOS 無效） |
| `menu.py` | 改 href | 網格卡片連結由 `play.html?game=<encoded slug>` 改為 **`play-<slug>.html`**（slug 為 ASCII，檔名安全，免 URL 編碼） |
| `easyrpg_web_build.py` | `build_library` | 把 `pwa.inject_play_game_info(out, entries)` 改成 `pwa.write_game_pages(out, entries, icon_rel)`（位置不變：menu 之後、manifest/SW 之前） |

`play.html` 仍保留於輸出（當模板來源），但選單不再連它。`pwa.write_service_worker`（最後執行）會自動把所有 `play-<slug>.html` 收進 precache。

### `write_game_pages` 行為細節
- `cover = entry["cover_rel"] or icon_rel`。
- title：移除模板中既有的 `<title>…</title>`（`re.sub`，count=1），再把新的 `<title>` + 兩個 icon `<link>` 注入 `</head>` 前。名稱用 `html.escape` 跳脫。
- game baked-in：`html.replace("game: undefined", "game: " + json.dumps(slug))`（slug ASCII；`json.dumps` 產生帶引號的字串字面值）。
- 寫出 `dist/play-{slug}.html`。

## 資料流

`build_library` → `library.stage_library` 回傳 entries（label/slug/cover_rel）→ `menu.write_menu`（網格，href 指向 `play-<slug>.html`）→ **`pwa.write_game_pages`（產各遊戲頁）** → manifest → service worker（最後，precache 含所有 `play-<slug>.html`）。

## 邊界處理
- 無封面 → icon 用庫主圖示。
- 模板若無 `<title>` → 直接注入新 title（`re.sub` 無命中則不動，再 inject）。
- slug 皆為 ASCII（既有 slugify 保證）→ 檔名 `play-<slug>.html` 安全。
- 單一遊戲 `build()` 不呼叫此函式 → 不受影響。

## 測試
- `tests/test_pwa_gamepages.py`（新增）：給含 `createEasyRpgPlayer({ game: undefined })`、`<title>X</title>`、`<head></head>` 的假 play.html 模板 + entries（一個有 cover、一個沒有）→ 產出 `play-<slugA>.html`、`play-<slugB>.html`；各含 `<title>遊戲名</title>`、`game: "<slug>"`；有封面者 icon 指向其 cover、無封面者指向 `icons/icon.png`。
- `tests/test_menu.py`（調整）：網格 href 改斷言 `href="play-<slug>.html"`。
- `tests/test_build_library.py`（調整）：移除/改寫原 `inject` 測試 → 改斷言 dist 內有 `play-<slug>.html`，內含對應遊戲名與封面；`test_build_library_two_games` 的 `play.html?game=` 斷言改成 `play-<slug>.html`。
- 移除 `tests/test_pwa_inject.py`（對應函式已移除）。
- 既有其餘測試不得退步。

## 上線 / 驗證
重打包＋重部署後，iPhone 無痕開遊戲庫 → 點遊戲 → **分頁標題＝遊戲名、分頁 icon＝封面**（靜態，iOS 應採用）。
> 「config.game 是否讓遊戲正確載入」無法在此用瀏覽器測（機制與 `?game=` 同一條路徑，信心高）；由使用者實機確認遊戲確實載入。

## 與既有的關係
- 取代上一輪的 `inject_play_game_info`（JS 注入）作法。
- 重用既有 entries（label/slug/cover_rel）與 `menu`/`library`，不改其資料介面。
