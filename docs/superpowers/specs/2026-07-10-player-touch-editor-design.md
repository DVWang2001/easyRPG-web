# 玩家端觸控按鍵編輯器

日期：2026-07-10　狀態：已定案（使用者核准方案 A）

## 目標

玩家在手機瀏覽器內自行編輯遊戲頁的觸控按鍵：拖拉移位、從鍵盤盤面新增（0–9、Shift、方向鍵、決定、取消、»、»»）、移除、還原預設。逐遊戲逐裝置保存（localStorage）。動機：月藍傳奇２等遊戲用到 0–9＋Shift 共 11 顆鍵，必須讓玩家能一鍵整排加入再微調。

不做站長端預設佈局（`wip/rm-redesign` 的 GUI 編輯器繼續冰存，兩者互不相干）。

## 架構

**單一新檔 `web/touchpad.js`**（ES module，遊戲頁載入）。建置端唯一改動＝`pwa.py` 的 `body_add` 加 `_TP_SNIPPET = '\n<script type="module" src="touchpad.js"></script>'`。工具列入口鈕與所有樣式由 touchpad.js 動態建立（不新增 css 檔、不改 `_SAVE_UI`）。`install_web_assets` 既有 `.js` 規則自動複製。

## 資料格式

`localStorage['ep-touch-<slug>']`：

```json
{"v":1,"buttons":[
  {"id":"dpad","x":2,"y":60},
  {"id":"apad-enter","x":88,"y":80},
  {"key":"Digit1","label":"1","x":52,"y":88}
]}
```

- 內建鍵以 `id` 引用：`dpad`（整組）、`apad-escape`、`apad-enter`、`apad-ff3`、`apad-ff10`；自訂鍵記 `key`（`event.code`）＋`label`。
- `x`/`y`＝視窗百分比（元素左上角），套用與拖拉時夾限 0–95。
- **沒有紀錄＝完全不動 vendor 預設**；有紀錄＝清單未列的內建鍵隱藏（排出來的就是全部）。
- `normalizeLayout(raw) → {v,buttons:[…]} | null` 純函式：驗證/夾限/丟壞項（localStorage 是不可信輸入）；export 供 node 測試。

## 套用（開頁）

- 內建鍵：inline `position:fixed; left/top:%; right/bottom:auto`；隱藏＝`display:none`。
- 自訂鍵：建立為 `#apad` 子元素（插在 `apad-escape` 前，保住 vendor `:last-child` 的 Enter 定位）→ 免費繼承圓鈕樣式、半透明/按壓規則、「觸控顯示／手把隱藏」邏輯。
- 自訂鍵綁定：touchstart→對 `#canvas` 派發 `keydown`（`event.code=key`）、touchend/touchcancel→`keyup`（與 vendor `simulateKeyboardEvent` 同語意；不做 vendor 的滑move換鍵）。

## 編輯模式

- 入口：`#saveui` 動態插入「🎮 按鍵」鈕，僅 `(hover: none), (pointer: coarse)` 顯示。
- 進入：`__epPause(true,'tp')`＋全畫面半透明罩；每顆鍵加高亮外框、單指拖拉移位（touchmove→%），拖進頂部「🗑 移除」區＝隱藏（內建）/刪除（自訂）。
- 底部盤面（水平捲動 chips）：`[方向鍵][決定][取消][Shift][0]…[9][0–9整排][»][»»]`；點擊＝加到畫面中央（已在畫面上的內建鍵 chip＝重新顯示）。`0–9整排`＝十顆等距排成一列加入。
- 動作列：`完成`（normalize→存→套用→退出）、`取消`（丟棄本次改動、回進入前狀態）、`還原預設`（刪除紀錄、移除所有 inline 覆寫與自訂鍵）。
- 鍵盤盤面鍵值：`Digit0..Digit9`、`ShiftLeft`(Shift)、`Enter`(決定)、`Escape`(取消)、`KeyF`(»)、`KeyG`(»»)、dpad＝內建組。

## 邊界

- 直橫向共用同一份百分比（不做雙佈局）。
- 編輯模式中不觸發遊戲輸入（遊戲已 `__epPause`；拖拉 handler `preventDefault`＋擋掉原 key 派發）。
- 壞資料 → `normalizeLayout` 回 null → 當作沒紀錄。
- 非觸控裝置：入口鈕不顯示；已存佈局仍套用（不傷桌機——vendor 本來就把 #dpad/#apad 隱藏）。

## 測試

- node：`normalizeLayout`（合法/壞欄位/夾限/未知 id/空清單）。
- pytest：遊戲頁含 `touchpad.js` snippet。
- 手機實測：加 0–9 整排＋Shift → 拖位 → 完成 → 重整保留 → 按鍵有作用（月藍２按鍵輸入）→ 還原預設。

## 不做（YAGNI）

直橫雙佈局、按鈕大小/透明度、雲端同步佈局、站長端預設佈局、自訂任意鍵碼輸入框。
