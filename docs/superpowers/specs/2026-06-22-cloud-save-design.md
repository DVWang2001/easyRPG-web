# 設計：雲端存檔（手動備份，Phase 2 最後一個）

日期：2026-06-22

## Context

Phase 2「個人化」已完成收藏、遊玩紀錄、個人頁。最後一個子功能是「雲端存檔同步」。經 brainstorming，
本輪做**手動雲端備份**（非自動同步）：使用者按鈕把本機存檔上傳到雲端、或從雲端取回，跨裝置靠這兩個
動作達成。自動同步與跨裝置衝突解析（風險高）列為非目標。

專案維持免費 Spark 方案（foundation spec 已把「Firebase Storage 需 Blaze」列非目標），故存檔存
**Firestore**，用 `Bytes` 型別、每個存檔格一份文件以避開 1MB/文件上限。

## 使用者決策（brainstorming 結論）

1. **手動**雲端備份（上傳/取回），不做自動同步。
2. 每遊戲、登入才可用；上傳＝本機覆蓋雲端、取回＝雲端覆蓋本機，兩者先確認。
3. 後端用 **Firestore（免費）**，存檔以 `Bytes` 存、每個 `SaveNN.lsd` 一份文件。

## 架構總覽

```
遊戲頁 play-<slug>.html
  ├─ _SAVE_UI（既有內嵌 JS）暴露 window.__epSaves = { read(), write(files) }
  │     read()  → [{ name, data:Uint8Array }]（讀 Save 資料夾）
  │     write(files) → 寫入 Save 資料夾 + syncfs（回 Promise）
  │     既有「導出/導入 zip」改用此 API（DRY）
  └─ 「☁ 雲端」鈕 → cloudsave.js（module，import account.js）開小面板
        ├─ 上傳：window.__epSaves.read() → 各檔 setDoc(.../files/<name>,{data:Bytes,updatedAt})
        └─ 取回：讀雲端 → window.__epSaves.write(files) → reload
Firestore（私有）
  ├─ users/<uid>/saves/<slug>            { updatedAt, names:[檔名…] }
  └─ users/<uid>/saves/<slug>/files/<檔名> { data:Bytes, updatedAt }
```

## 元件設計

### `_SAVE_UI`（`pwa.py`）重構：暴露 `window.__epSaves`

- 現有 `readSaves()`、`saveDir()`、寫檔＋`syncfs` 邏輯在 `_SAVE_UI` 閉包內。抽成：
  - `window.__epSaves.read()` → 回 `[{ name, data:Uint8Array }]`（無存檔回 `[]`）。
  - `window.__epSaves.write(files)` → `mkdirp` 目標 Save 目錄、逐檔 `FS.writeFile`、`FS.syncfs(false, …)`；
    回 `Promise`（resolve 於 syncfs 完成）。
- **既有導出 zip**：`makeZip(window.__epSaves.read())`；**既有導入 zip**：`window.__epSaves.write(files).then(reload)`。
  行為不變，只是共用同一份 FS 存取邏輯。
- `read`/`write` 在遊戲未載入（`mod()` 為 null）時：`read()` 回 `[]`、`write` reject／回空，呼叫端提示。

### `web/firestore.rules`（擴充）

私有：
```
match /users/{uid}/saves/{slug} {
  allow read, write: if request.auth != null && request.auth.uid == uid;
  match /files/{name} {
    allow read, write: if request.auth != null && request.auth.uid == uid;
  }
}
```
（存檔是本人私有資料；欄位不嚴格白名單以容納 Bytes，但維持本人讀寫。）

### `web/cloudsave.js`（ES module，`import account.js`）

- `import { db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser } from './account.js';`
- `import { doc, getDoc, getDocs, setDoc, deleteDoc, collection, serverTimestamp, Bytes } from '…/firebase-firestore.js';`
- 讀 `window.__WT.slug`。
- 「☁ 雲端」鈕（`#cloud-open`）→ 開小面板（仿攻略浮層；開時 `window.__epPause(true,'cloud')`、關時 `false`）：
  - 登入狀態（未登入→「用 Google 登入」；已登入→名字＋登出）。
  - 「上次雲端備份：<時間>」（讀父文件 `updatedAt`；無則「尚未備份」）。
  - **上傳到雲端**（先 `confirm`）：`const files = window.__epSaves.read()`；空→提示「先在遊戲裡存檔」；
    每檔 `setDoc(doc(db,'users',uid,'saves',slug,'files',name), { data: Bytes.fromUint8Array(data), updatedAt: serverTimestamp() })`；
    刪掉雲端多出來的舊檔（比對現有 names）；更新父文件 `setDoc(.../saves/slug, { updatedAt: serverTimestamp(), names })`。
  - **從雲端取回**（先 `confirm`，會覆蓋本機）：讀父文件 names（無→提示「雲端沒有存檔」）；逐檔 `getDoc` 取
    `snap.data().data.toUint8Array()` 組成 `[{name,data}]`；`await window.__epSaves.write(files)`；成功→
    `location.reload()`。
  - 每檔大小上限 900KB（超過→略過該檔＋提示；RPG Maker 存檔遠小於此）。
- 後端未設定（`!isReady()`）→ 面板提示「站長尚未設定後端」。

### `web/cloudsave.css`

小面板樣式（仿攻略/留言深色浮層）、雲端鈕、上傳/取回鈕、狀態列。

### `pwa.py` 注入

- `_SAVE_UI` 的 `#saveui` 加 `<button id="cloud-open">☁ 雲端</button>`。
- 新增 `_CLOUD_SNIPPET`：`cloudsave.css` link ＋ `cloudsave.js` module script，接到 `body_add`。
- `cloudsave.js`/`cloudsave.css` 由 `install_web_assets` 自動複製。

## 資料流

1. 點「☁ 雲端」→ 面板開、暫停遊戲、讀父文件顯示上次備份時間。
2. 上傳：讀本機存檔 → 寫各檔 Bytes ＋ 父文件 names → 顯示「已上傳」。
3. 取回：讀雲端各檔 → 寫本機 + syncfs → reload（遊戲帶新存檔重啟）。

## 錯誤處理

- 未登入→引導登入；`!isReady()`→面板提示；遊戲未載入→「請稍候」。
- 上傳找不到本機存檔→「先在遊戲裡存檔」。
- 取回時雲端無存檔→提示。
- 任一 Firestore 失敗→`alert` 友善訊息、不破壞本機存檔（取回失敗就不 reload）。
- 超過大小上限的檔→略過＋提示。

## 測試

- **Python（自動）**：`pwa.write_game_pages` 注入 `id="cloud-open"`、`cloudsave.css`/`cloudsave.js` 引用、
  頁面含 `window.__epSaves`；`install_web_assets` 複製 `cloudsave.js`/`cloudsave.css`；既有導出/導入測試仍綠
  （重構不改行為）。
- **JS 語法**：`node --check`（`cloudsave.js`；`_SAVE_UI` 內嵌 JS 也 node --check）。
- **手動**：登入→A 裝置上傳存檔→B 裝置（或無痕）取回→遊戲帶到該存檔；未登入只提示；取回前確認。

## 非目標（YAGNI）

- 自動同步、跨裝置衝突解析、雲端多版本/歷史回溯。
- 跨遊戲一鍵全備份、選擇性單格備份（本輪整包上傳/取回）。
- Firebase Storage（不啟用 Blaze）；改用 Storage 之後若存檔變大再議。

## 前置依賴

需站長已設好 Firebase 並**發布 Firestore 規則**（本輪規則為擴充，須一併重新發布）。
