# 觸控快轉鈕（F ×3／G ×10）

日期：2026-07-10　狀態：已定案（使用者核准）

## 目標

觸控裝置的遊戲頁右下角、Esc/Enter 鈕上方，內建兩顆快轉鈕：`»`（按住＝送 KeyF＝Player 快轉 ×3）、`»»`（按住＝送 KeyG＝超快轉 ×10）。放手即恢復原速。全站每款遊戲都有。

## 做法

`pwa.py` `write_game_pages`：在 `#apad` 內、`apad-escape` **之前**注入（插 apad-enter 之後會搶走 vendor CSS `:last-child` 的 Enter 鈕定位）：

```html
<div id="apad-ff3" class="unselectable" data-key="KeyF" title="快轉 ×3">»</div>
<div id="apad-ff10" class="unselectable" data-key="KeyG" title="快轉 ×10">»»</div>
```

- vendor 殼自動把 `[data-key]` 綁成按住 keydown／放開 keyup；EasyRPG Player 預設 F/G 即 ×3/×10 → 零新 JS。
- 在 `#apad` 內 → 觸控才顯示、接手把/鍵盤自動隱藏（跟 dpad 同進退）；半透明/按下實色也繼承 vendor 規則。
- CSS（注入 head）：兩顆 0.6×`--controls-size`、`position:fixed` 橫排疊在 Esc/Enter 上方（`bottom: 1rem+2.2×size`，`»»` 靠右、`»` 在其左）。
- 不進 `_TOUCH_BUILTIN_IDS`：與逐遊戲 touch_layout 互不干涉，編輯器不管它、永遠顯示。
- 找不到 anchor 就整段跳過（沿用容錯慣例）。

## 不做（YAGNI）

切換式快轉、自訂倍速、觸控編輯器支援移動/刪除這兩顆。

## 風險

G（FAST_FORWARD_PLUS）若此版 player 未支援 → 只留 `»`。實測驗證。

## 測試

`tests/test_pwa_gamepages.py` 新增斷言：兩顆鈕存在、`data-key="KeyF"/"KeyG"`、出現在 `apad-escape` 之前、CSS 有注入。手機（或 DevTools 觸控模擬）實測按住快轉。
