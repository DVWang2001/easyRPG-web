# 設計：開啟存檔/攻略面板時暫停遊戲

日期：2026-06-21

## Context

遊戲頁左上角有「導出存檔／導入存檔」鈕（pwa 注入的內嵌 JS，`pwa._SAVE_UI`）與「攻略」面板
（`web/walkthrough.js`）。這些 UI 浮在 EasyRPG 遊戲畫面上時，**遊戲仍在背景執行**（繼續跑、
吃鍵盤、流逝遊戲時間/音樂）。使用者希望在**導出存檔、導入存檔、寫攻略**時暫停遊戲，結束後恢復。

## 可行性（已查證）

EasyRPG 的 emscripten Module 有匯出
`Module["pauseMainLoop"] = MainLoop.pause` 與 `Module["resumeMainLoop"] = MainLoop.resume`
（見 `players/official/index.js`）。所以呼叫 `easyrpgPlayer.pauseMainLoop()` 會凍結主迴圈
（畫面/邏輯/輸入），`resumeMainLoop()` 恢復。`easyrpgPlayer` 是遊戲頁全域變數。

## 設計

### 共用暫停機制（window 計數器）

存檔面板（內嵌 JS）與攻略面板（`walkthrough.js`）是兩段獨立腳本，但同頁共用 `window`。用一個
計數器協調，避免一邊關閉就把另一邊也恢復：

- `window.__epPause(on)`：`on===true` → 計數 +1；`on===false` → 計數 −1（不低於 0）。
- 計數由 0→1 時呼叫 `easyrpgPlayer.pauseMainLoop()`；由 1→0 時呼叫 `resumeMainLoop()`。
- 兩個方法都先檢查 `typeof easyrpgPlayer !== 'undefined' && easyrpgPlayer && 該方法存在` 才呼叫
  （遊戲未載入完就略過，不報錯）。
- 此 helper 由**先載入的存檔內嵌 JS** 定義在 `window.__epPause`；`walkthrough.js` 直接用
  `window.__epPause`（若不存在則 no-op 防呆）。

### 各情境

- **寫攻略**（`walkthrough.js`）：面板 `openPanel()` → `__epPause(true)`；`closePanel()` →
  `__epPause(false)`。
- **導入存檔**（`_SAVE_UI`）：按「導入」`inp.click()` 前 `__epPause(true)`；
  - 若選了檔 → 走既有流程（寫入→syncfs→`location.reload()`，遊戲本來就重來，不需手動恢復）。
  - 若取消檔案視窗（沒觸發 `onchange`）→ 在視窗重新取得焦點時恢復：`inp.click()` 後掛一次性
    `window.addEventListener('focus', once)`，`once` 內若尚未開始匯入則 `__epPause(false)`。
- **導出存檔**（`_SAVE_UI`）：導出是同步、瞬間觸發下載；在動作前 `__epPause(true)`、`a.click()`
  之後 `__epPause(false)`（實際上感覺不到，為一致性保留）。

### 音樂

暫停主迴圈通常連音訊更新一起停。若實測音樂仍播放，再加 `AudioContext.suspend()`/`resume()`
（本輪 YAGNI，先不做）。

## 錯誤處理／邊界

- `easyrpgPlayer` 尚未就緒：暫停/恢復皆 no-op，不報錯。
- 重複暫停（理論上面板互斥，但仍用計數器）：恢復只在計數歸零時發生，避免提早恢復。
- 全螢幕切換不影響（暫停與顯示無關）。

## 測試

- `node --check`（語法）。
- 手動：開攻略面板→遊戲凍結（角色不動、輸入無效）；關閉→繼續。導入按下→暫停；取消檔案視窗
  →恢復。導出→無感（瞬間）。

## 非目標（YAGNI）

- `AudioContext` 細部靜音（先靠主迴圈暫停）。
- 暫停時顯示「已暫停」遮罩或提示（面板本身就在前面）。
