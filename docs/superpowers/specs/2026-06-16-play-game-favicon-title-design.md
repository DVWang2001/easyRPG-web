# 點進遊戲後：分頁標題＝遊戲名、favicon＝封面

- 狀態：已通過設計討論，待寫實作計畫
- 日期：2026-06-16
- 專案：`C:\opensource\easyRPG-web\`（分支 `feat/play-game-favicon-title`，建立在已完成的多遊戲庫之上）

## 背景與目標

多遊戲庫中，點選某遊戲會開 `play.html?game=<slug>`（共用的 EasyRPG player 頁）。目前所有遊戲共用同一個分頁標題與 favicon（遊戲庫的）。使用者希望：**進入某遊戲後，瀏覽器分頁的標題變成該遊戲名稱、favicon 變成該遊戲封面。**

**關鍵限制：** `?game=` 只帶 slug（ASCII，如 `game-2`），不含顯示名稱；且**不能**在網址加其他 query 參數帶名稱 —— EasyRPG player 的 `parseArgs` 會把多餘的 `?key=value` 當成 `--key value` 傳給引擎，可能出錯。故改用**把對照表注入 play.html**。

**目標**
- `play.html` 載入時依 `?game=<slug>` 設定 `document.title` 為該遊戲名稱、favicon 為該遊戲封面。
- 沒封面的遊戲 → favicon 維持遊戲庫主圖示（自動 fallback，不破圖）。
- 選單頁 `index.html` 維持「遊戲庫名稱 + 主圖示」不變。

**非目標**
- 每遊戲各自的「加入主畫面」PWA 圖示（整個庫是單一 PWA，home-screen 圖示仍是庫的主圖示）。
- 用遊戲 Title 畫面當來源（採封面圖）。
- 單一遊戲 `build()` 流程（不變）。

## 設計

### 注入的 script（在 `play.html` 內）
build 時把一份 slug→資訊對照表與切換邏輯注入 `play.html` 的 `<head>`：
```html
<script>
window.__EASYRPG_GAMES__ = {
  "game":   { "name": "花嫁之冠", "cover": "games/game/cover.png" },
  "game-2": { "name": "勇者傳說" }
};
(function () {
  var slug = new URLSearchParams(location.search).get("game");
  if (!slug) return;
  var info = window.__EASYRPG_GAMES__[slug];
  if (!info) return;
  if (info.name) document.title = info.name;
  if (info.cover) {
    var img = new Image();
    img.onload = function () {
      var link = document.querySelector("link[rel~='icon']") || document.createElement("link");
      link.setAttribute("rel", "icon");
      link.setAttribute("href", info.cover);
      document.head.appendChild(link);
    };
    img.src = info.cover; // 載入成功才換 → 缺封面則維持原 favicon
  }
})();
</script>
```
- `name` 一定有；`cover` 僅在該遊戲有封面（`cover_rel` 非空）時存在。
- 對照表以 `json.dumps(..., ensure_ascii=False)` 產生，並把 `<` 轉成 `<` 以防 `</script>` 注入。

### 元件 / 改動（只動 easyRPG-web）
| 檔案 | 變更 | 說明 |
|---|---|---|
| `pwa.py` | 新增 `inject_play_game_info(dist, entries)` | 讀 `dist/play.html`，把對照表＋script 注入 `</head>` 前（無 `</head>` 則 `</body>` 前）。`entries` 元素為 `{label, slug, cover_rel}`；map 值為 `{name: label, cover: cover_rel?}` |
| `easyrpg_web_build.py` | `build_library` 加一步 | 在 `menu.write_menu(...)` 之後、`write_manifest`/`write_service_worker` 之前，呼叫 `pwa.inject_play_game_info(out, entries)`（此時 play.html 已存在、entries 已算出） |

> 順序：service worker 仍最後寫，會把含注入 script 的 `play.html` precache 進去。

### 資料流
`build_library` → `library.stage_library` 回傳 entries（含 label/slug/cover_rel）→ `menu.write_menu(entries)`（網格）→ **`pwa.inject_play_game_info(out, entries)`（注入 play.html）** → manifest → service worker。

## 邊界處理
- `play.html` 不帶 `?game`（理論上不會發生，因都從網格點入）→ script 直接 return，維持預設標題/圖示。
- slug 不在對照表 → return，不改。
- 遊戲無封面 → 對照表該項無 `cover` → favicon 不變（維持主圖示）。
- 名稱含特殊字元 → 由 `json.dumps` 安全序列化；額外把 `<` 轉義避免關閉 script。
- 單一遊戲 `build()` 不呼叫此函式 → 行為不變。

## 測試
- `tests/test_pwa.py`（或既有 pwa 測試檔）新增 `test_inject_play_game_info`：給一個含 `<head></head>` 的假 play.html 與 entries（一個有 cover、一個沒有）→ 注入後 play.html 含 `__EASYRPG_GAMES__`、兩個遊戲名稱、有封面者含其 cover 路徑、且含設定 `document.title` 與 `link rel='icon'` 的邏輯。
- `tests/test_build_library.py` 端對端：`build_library` 後 `play.html` 含某遊戲名稱與其封面路徑於對照表中。
- 既有測試不得退步。

## 上線
實作完需重打包＋重部署遊戲庫才生效。亦可由開發者直接對已部署的 `play.html` 補上同一段 script（已知 6 個遊戲的 slug→名稱）。

## 與既有的關係
- 重用既有 `build_library`/`menu`/`library` 產生的 entries（label/slug/cover_rel），不改其介面。
- 不動 `library.py`（封面路徑經 entries 帶入對照表，副檔名沿用現狀）。
