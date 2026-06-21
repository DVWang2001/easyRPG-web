# 設計：遊戲收藏（Phase 2 第一個）

日期：2026-06-22

## Context

社群地基（Phase 0）與 Phase 1（攻略、留言、評分）已完成。Phase 2「個人化」拆成 4 個獨立
子功能（收藏、遊玩紀錄、個人頁、雲端存檔同步）；本輪做**第一個：遊戲收藏**。

收藏疊在既有地基上（`import account.js`）。與攻略/留言（注入各遊戲頁）不同，收藏**第一次需要在
遊戲庫首頁 `index.html`（由 `menu.py` 產生）加 UI**，並同時在遊戲頁加一顆 ❤。

完整藍圖見 `2026-06-21-walkthroughs-foundation-design.md`。

## 使用者決策（brainstorming 結論）

1. ❤ 收藏鈕：**首頁卡片＋遊戲頁都有**。
2. 看收藏：首頁工具列加「**❤ 只看收藏**」篩選（沿用既有卡片隱藏機制），不另開頁。
3. 收藏**私有**（只有本人讀寫，別人看不到）。
4. **不做排序**（本輪 YAGNI）；收藏照首頁原順序顯示。資料仍存 `addedAt`，之後要排序再加。

## 架構總覽

```
遊戲庫首頁 index.html（menu.py 產生）
  ├─ 工具列「❤ 只看收藏」鈕 + CSS: body.favonly .card:not(.is-fav){display:none}
  └─ favorites.js（module）→ import account.js
        ├─ 讀 users/<uid>/favorites（登入後）
        ├─ 每張卡片塞 ❤ 鈕、已收藏的卡片加 .is-fav
        └─ 「只看收藏」切換 body.favonly
遊戲頁 play-<slug>.html（pwa.py 注入）
  └─ #saveui 內 ❤ 鈕(#fav-btn) ← favorites.js 同一支處理（讀 window.__WT.slug）
Firestore
  └─ users/<uid>/favorites/<slug>  { addedAt }   （slug＝doc id；私有）
```

## 元件設計

### 資料模型（Firestore）

- `users/<uid>/favorites/<slug>` = `{ addedAt: serverTimestamp() }`，slug 當 doc id（天然去重、易查單筆）。

### `web/firestore.rules`（擴充）

在 `match /databases/{database}/documents` 內、與 `match /games/{slug}/...` 同層新增：

```
// 收藏：完全私有，只有本人能讀寫；欄位只允許 addedAt。
match /users/{uid}/favorites/{slug} {
  allow read: if request.auth != null && request.auth.uid == uid;
  allow write: if request.auth != null && request.auth.uid == uid
    && (request.resource.data == null
        || request.resource.data.keys().hasOnly(['addedAt']));
}
```

（`allow write` 同時涵蓋 create/update/delete；刪除時 `request.resource.data == null`，故放行刪除。）

### `web/favorites.js`（ES module，新增）

一支同時處理兩種情境，靠頁面元素判斷：

- `import { db, isReady, currentUser, onAuthChange, signInWithGoogle } from './account.js';`
- `import { collection, doc, getDocs, setDoc, deleteDoc, serverTimestamp } from '…/firebase-firestore.js';`
- 啟動時：若 `!isReady()` → 直接 return（後端未設定，不掛任何 ❤）。
- **模組狀態**：`const favs = new Set()`（目前使用者已收藏的 slug）。
- **首頁情境**（存在 `#grid`）：
  - 收集卡片：`document.querySelectorAll('#grid .card')`，每張卡片的 slug 從 `href`（`play-<slug>.html`）解析。
  - 在每張卡片塞一顆 ❤ 鈕（`button.fav-btn`，絕對定位於角落）；點擊 `e.preventDefault(); e.stopPropagation();`（防止觸發卡片連結）→ `toggleFav(slug)`。
  - 工具列「只看收藏」鈕（`#favonly`，由 menu.py 靜態加入）：點擊切換 `document.body.classList.toggle('favonly')` 並更新鈕的 active 樣式。
- **遊戲頁情境**（存在 `#fav-btn`）：該鈕顯示 `window.__WT.slug` 的收藏狀態，點擊 → `toggleFav(slug)`。
- **共用**：
  - `loadFavs()`：登入時 `getDocs(collection(db,'users',uid,'favorites'))` → 填 `favs` → `renderAll()`；未登入 → 清空 `favs` → `renderAll()`。
  - `renderAll()`：依 `favs` 設每顆 ❤ 的 on/off 與卡片的 `.is-fav`。
  - `toggleFav(slug)`：未登入 → `signInWithGoogle()`；已登入 → 先樂觀更新 UI，再 `setDoc(doc(db,'users',uid,'favorites',slug),{addedAt:serverTimestamp()})`（加入）或 `deleteDoc(…)`（移除）；失敗 → 還原 UI＋輕提示。
  - `onAuthChange(loadFavs)`：登入/登出都重載收藏狀態。

### `web/favorites.css`（新增）

❤ 鈕樣式（卡片角落絕對定位、空心/實心兩態）、`#favonly` 工具列鈕、`#fav-btn` 遊戲頁鈕（與
`#saveui` 其他鈕一致）。`body.favonly .card:not(.is-fav){display:none}` 放在 menu.py 的首頁 CSS
（與既有 `.card[hidden]` 規則並存：兩者皆用 display 隱藏，搜尋/標籤篩選與「只看收藏」自然疊加）。

### `menu.py`（首頁注入）

- 工具列（`<div class="toolbar">…</div>`）內、`清除篩選` 之後加入 `<button id="favonly">❤ 只看收藏</button>`。
- 首頁 `<style>` 加 `body.favonly .card:not(.is-fav){display:none}` 與 ❤ 定位所需的 `.card{position:relative}`。
- `<head>`/`<body>` 末端加入 `<link rel="stylesheet" href="favorites.css">` 與 `<script type="module" src="favorites.js"></script>`。

### `pwa.py`（遊戲頁注入）

- `_SAVE_UI` 的 `#saveui` 按鈕列加 `<button id="fav-btn" title="收藏">♡</button>`（與攻略/留言/存檔同排，沿用全螢幕隱藏）。
- 注入 `<link rel="stylesheet" href="favorites.css">` 與 `<script type="module" src="favorites.js"></script>`（沿用既有片段機制）。
- `install_web_assets` 自動複製 `web/*.js`/`*.css` → `favorites.js`/`favorites.css` 自動進 dist，無需改該函式。

## 資料流

1. 首頁/遊戲頁載入 → `favorites.js` 啟動（`isReady` 才繼續）→ `onAuthChange`。
2. 登入後 → `loadFavs()` 讀 `users/<uid>/favorites` → 標記 ❤/`.is-fav`。
3. 點 ❤：未登入→登入；已登入→樂觀更新＋`setDoc`/`deleteDoc`。
4. 首頁「只看收藏」→ 切 `body.favonly` → CSS 與既有篩選疊加，只剩已收藏卡片。

## 錯誤處理

- 後端未設定（`isReady` false）→ favorites.js 啟動時先**隱藏 `#favonly`**（`el.hidden = true`）再 return，
  不掛 ❤、不留下點了無效的死鈕。
- 未登入點 ❤ → 觸發登入。
- 讀收藏失敗（網路/規則）→ `favs` 留空、❤ 全空、不丟未捕捉錯誤。
- 寫入失敗 → 還原該顆 ❤ 與 `.is-fav`、`alert` 輕提示。

## 測試

- **Python（自動）**：
  - `menu.write_menu` 產出的 index.html 含 `id="favonly"`、`favorites.css`/`favorites.js` 引用、`favonly` CSS 規則。
  - `pwa.write_game_pages` 注入 `id="fav-btn"`、`favorites.css`/`favorites.js` 引用。
  - `pwa.install_web_assets` 複製 `favorites.js`/`favorites.css` 進 dist。
- **JS 語法**：`node --check`（`favorites.js`）。
- **前端/規則（手動）**：登入→首頁卡片收藏一個→「只看收藏」只剩它→遊戲頁 ❤ 同步顯示→另一帳號看不到你的收藏→未登入點 ❤ 觸發登入。

## 非目標（YAGNI）

- 收藏排序/分類。
- 收藏公開給別人看（本輪純私有）。
- 個人頁、遊玩紀錄、雲端存檔同步（各為後續輪次）。
- 收藏數統計（誰收藏了幾次）。

## 已知小取捨

- 首頁 ❤ 是塞進 `<a class="card">` 內的 `<button>`（嚴格說互動元素不該放錨點內）；靠
  `preventDefault`+`stopPropagation` 確保不誤觸卡片連結（與既有 `.card .tag` 點擊處理同一手法）。
  實務可行，標為已知小瑕；日後若要嚴謹可把卡片改為 `<div>`＋內層連結。

## 前置依賴

與既有相同：站長已設好 Firebase 並**發布 Firestore 規則**（本輪規則為擴充，須一併重新發布）。
