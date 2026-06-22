# 設計：存檔面板（本機 zip ＋ 雲端手動備份，Phase 2 最後一個）

日期：2026-06-22

## Context

Phase 2「個人化」已完成收藏、遊玩紀錄、個人頁。最後一個子功能是「雲端存檔同步」。經 brainstorming，
本輪做**手動雲端備份**（非自動同步）。並依使用者要求，把現有的「導出存檔/導入存檔」與新的「雲端上傳/
取回」**收進同一個「存檔」面板**——`#saveui` 由兩顆存檔鈕改為一顆「存檔」鈕開面板。

專案維持免費 Spark 方案（foundation spec 已把「Firebase Storage 需 Blaze」列非目標），故存檔存
**Firestore**，用 `Bytes` 型別、每個存檔格一份文件以避開 1MB/文件上限。

## 使用者決策（brainstorming 結論）

1. **手動**雲端備份（上傳/取回），不做自動同步。
2. 導出/導入 zip 與雲端上傳/取回**收進同一個「存檔」面板**。
3. 每遊戲；雲端動作需登入；上傳＝本機覆蓋雲端、取回＝雲端覆蓋本機，兩者先確認。
4. 後端用 **Firestore（免費）**，存檔以 `Bytes` 存、每個 `SaveNN.lsd` 一份文件。

## 架構總覽

```
遊戲頁 play-<slug>.html（#saveui 一顆「存檔」鈕 #save-open）
  ├─ _SAVE_UI（既有內嵌 classic JS）
  │     ├─ 「存檔」面板 #savepanel（開時 __epPause('save')）：導出 zip / 導入 zip / #sp-cloud 容器（給雲端模組填）
  │     ├─ 導出/導入 zip 用既有 FS+zip 邏輯（本機，免後端）
  │     └─ 暴露 window.__epSaves = { read(), write(files) } 供雲端模組共用
  └─ savepanel.js（module，import account.js）
        └─ 把雲端區塊填進 #sp-cloud：登入狀態、上次備份時間、上傳到雲端、從雲端取回
Firestore（私有）
  ├─ users/<uid>/saves/<slug>             { updatedAt, names:[檔名…] }
  └─ users/<uid>/saves/<slug>/files/<檔名> { data:Bytes, updatedAt }
```

## 元件設計

### `_SAVE_UI`（`pwa.py`）：改為「存檔」面板 ＋ 暴露 `window.__epSaves`

- `#saveui` 把 `<button id="saveexp">導出存檔</button><button id="saveimp">導入存檔</button>` 兩顆
  換成一顆 `<button id="save-open">存檔</button>`。
- 新增 `#savepanel`（hidden 浮層，仿攻略：背景遮罩＋對話框，✕/點旁邊關）。內含：
  - 「導出存檔」鈕（zip 下載，既有邏輯）、「導入存檔」鈕（zip 上傳，既有邏輯）、隱藏 `<input type=file>`。
  - 空容器 `<div id="sp-cloud"></div>`（雲端模組 savepanel.js 在此塞入雲端 UI）。
- `#save-open` 點擊 → 開 `#savepanel` ＋ `window.__epPause(true,'save')`；✕/遮罩關 → `false`。
- 既有 `readSaves()`/`saveDir()`/寫檔＋`syncfs` 邏輯抽成並暴露：
  - `window.__epSaves.read()` → `[{ name, data:Uint8Array }]`（無存檔或遊戲未載入回 `[]`）。
  - `window.__epSaves.write(files)` → `mkdirp`＋逐檔 `FS.writeFile`＋`FS.syncfs(false,…)`，回 `Promise`。
  - 導出鈕＝`makeZip(window.__epSaves.read())` 下載；導入鈕＝讀 zip→`window.__epSaves.write(files).then(reload)`。
    （行為不變，只是收進面板並共用同一份 FS 存取。）

### `web/firestore.rules`（擴充）

私有（存檔是本人資料）：
```
match /users/{uid}/saves/{slug} {
  allow read, write: if request.auth != null && request.auth.uid == uid;
  match /files/{name} {
    allow read, write: if request.auth != null && request.auth.uid == uid;
  }
}
```

### `web/savepanel.js`（ES module，`import account.js`）

- `import { db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser } from './account.js';`
- `import { doc, getDoc, getDocs, setDoc, deleteDoc, collection, serverTimestamp, Bytes } from '…/firebase-firestore.js';`
- 讀 `window.__WT.slug`。找不到 `#sp-cloud` 容器（理論上一定有）→ 直接 return。
- 在 `#sp-cloud` 渲染雲端區塊：
  - 登入狀態（未登入→「用 Google 登入」；已登入→名字＋登出）。
  - 「上次雲端備份：<時間>」（讀父文件 `updatedAt`；無→「尚未備份」）。
  - **上傳到雲端**（需登入；先 `confirm`）：`const files = window.__epSaves.read()`；空→「先在遊戲裡存檔」；
    每檔（≤900KB，超過略過＋提示）`setDoc(doc(db,'users',uid,'saves',slug,'files',name),{data:Bytes.fromUint8Array(data),updatedAt:serverTimestamp()})`；
    刪掉雲端多出來的舊檔（比對 names）；更新父文件 `setDoc(.../saves/slug,{updatedAt:serverTimestamp(),names})`。
  - **從雲端取回**（需登入；先 `confirm`，會覆蓋本機）：讀父文件 names（無→「雲端沒有存檔」）；逐檔
    `getDoc` 取 `snap.data().data.toUint8Array()` 組 `[{name,data}]`；`await window.__epSaves.write(files)`→`location.reload()`。
- `!isReady()`：`#sp-cloud` 顯示「雲端功能需站長設定後端」（本機導出/導入 zip 仍可用，因在面板裡、不需後端）。

### `web/savepanel.css`

「存檔」面板浮層（仿攻略/留言深色）、面板內各鈕、雲端狀態列樣式。

### `pwa.py` 注入

- `_SAVE_UI` 改 `#saveui` 鈕列（存檔鈕取代導出/導入）＋ `#savepanel` 面板 ＋ 暴露 `window.__epSaves`（皆在內嵌 JS）。
- 新增 `_CLOUD_SNIPPET`：`savepanel.css` link ＋ `savepanel.js` module script，接到 `body_add`。
- `savepanel.js`/`savepanel.css` 由 `install_web_assets` 自動複製。

## 資料流

1. 點「存檔」→ 面板開、暫停遊戲；雲端模組讀父文件顯示上次備份時間。
2. 導出/導入 zip：本機，行為同現況。
3. 上傳：讀本機存檔 → 寫各檔 Bytes ＋ 父文件 names。
4. 取回：讀雲端各檔 → 寫本機 + syncfs → reload。

## 錯誤處理

- 未登入點雲端→引導登入；`!isReady()`→雲端區塊提示、zip 仍可用；遊戲未載入→「請稍候」。
- 上傳找不到本機存檔→「先在遊戲裡存檔」；取回時雲端無存檔→提示。
- 任一 Firestore 失敗→`alert` 友善訊息、不破壞本機存檔（取回失敗就不 reload）。
- 超過 900KB 的檔→略過＋提示。

## 測試

- **Python（自動）**：`pwa.write_game_pages` 注入 `id="save-open"`、`id="savepanel"`、`id="sp-cloud"`、
  `savepanel.css`/`savepanel.js` 引用、頁面含 `window.__epSaves`；不再有獨立 `id="saveexp"`/`id="saveimp"` 於
  `#saveui` 按鈕列（改在面板內）；`install_web_assets` 複製 `savepanel.js`/`savepanel.css`。
- **JS 語法**：`node --check`（`savepanel.js` 與 `_SAVE_UI` 內嵌 JS）。
- **手動**：開「存檔」面板 → 導出/導入 zip 同現況；登入→上傳→另一裝置/無痕取回→遊戲帶到該存檔；
  未登入只提示；上傳/取回前確認。

## 非目標（YAGNI）

- 自動同步、跨裝置衝突解析、雲端多版本/歷史回溯。
- 跨遊戲一鍵全備份、選擇性單格備份（本輪整包上傳/取回）。
- Firebase Storage（不啟用 Blaze）。

## 前置依賴

需站長已設好 Firebase 並**發布 Firestore 規則**（本輪規則為擴充，須一併重新發布）。
