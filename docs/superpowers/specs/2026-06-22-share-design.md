# 設計：分享遊戲（Phase 4 第一個）

日期：2026-06-22

## Context

Phase 0–3 已完成。Phase 4「站務」先做最單純、最獨立的「分享」：在遊戲頁分享該遊戲的網址＋名稱。
用瀏覽器原生 `navigator.share`（手機叫出系統分享單），桌機/不支援則複製連結。**不需後端、不需
Firestore、不需規則、不需新檔**——只是一個原生 API 呼叫，全部寫在既有 `pwa.py` 的 `_SAVE_UI` 內嵌 JS。

## 使用者決策（brainstorming 結論）

1. Phase 4 先做**分享**。
2. 分享鈕放在遊戲頁 `#saveui` 的**留言右邊**（成為最右一顆）。順序：`存檔、❤、已遊玩、攻略、留言、分享`。

## 元件設計

### `pwa.py` 的 `_SAVE_UI`（內嵌 classic JS）

- `#saveui` 按鈕列在 `<button id="cm-open">留言</button>` 之後加 `<button id="share-btn">分享</button>`（最右）。
- 在 `_SAVE_UI` 的 IIFE 內加點擊處理（讀值在 click 當下，故 `window.__WT` 已由稍後的 `_WT_SNIPPET` 設好）：
  ```js
  document.getElementById("share-btn").onclick = function () {
    var t = (window.__WT && window.__WT.title) || document.title;
    var u = location.href;
    if (navigator.share) {
      navigator.share({ title: t, url: u }).catch(function () {});
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(u).then(
        function () { alert("已複製連結"); },
        function () { prompt("複製這個連結：", u); }
      );
    } else {
      prompt("複製這個連結：", u);
    }
  };
  ```
- 不需 module、不需 account.js/Firestore。

## 資料流
- 點「分享」→ 取 `window.__WT.title`／`document.title` 與 `location.href` → `navigator.share` 或剪貼簿/`prompt`。

## 錯誤處理
- `navigator.share` 被使用者取消或失敗 → `.catch` 安靜略過。
- `navigator.clipboard.writeText` 失敗（權限/HTTP）→ 退回 `prompt` 顯示網址讓使用者自行複製。
- 兩者皆無 → `prompt` 顯示網址。

## 測試
- **Python（自動）**：`pwa.write_game_pages` 注入 `id="share-btn"` 與 `navigator.share`；
  且 `share-btn` 在 `cm-open` 之後（最右）。
- **JS 語法**：`_SAVE_UI` 內嵌 JS 過 `node --check`。
- **手動**：手機按「分享」→ 系統分享單帶遊戲名/網址；桌機按「分享」→ 複製連結＋提示。

## 非目標（YAGNI）
- 首頁卡片分享。
- 特定平台專屬按鈕（FB/Line：原生分享單已涵蓋）。
- 自訂分享縮圖/描述（OG meta 另議）。
- 好看的 toast（用 alert/prompt 即可）。

## 前置依賴
- 無（純前端原生 API；不動規則、不需重發 Firestore 規則，只需重建部署）。
- `navigator.share`/`clipboard` 多數需 HTTPS——GitHub Pages 已是 HTTPS。
