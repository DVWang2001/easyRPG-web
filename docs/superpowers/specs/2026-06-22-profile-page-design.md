# 設計：個人頁 profile.html（Phase 2）

日期：2026-06-22

## Context

Phase 2「個人化」已完成「收藏」與「遊玩紀錄（playtime）」。本輪做「個人頁」——把使用者自己的
資料集中到一頁。這是專案**第一個獨立新頁面**（前幾輪都是注入既有頁）。

本版只放**我的收藏 ＋ 最近遊玩**（「我的投稿」需 collectionGroup 跨遊戲查詢＋索引，留後續輪次）。
收藏與遊玩紀錄的 Firestore 規則**已允許本人讀取**，故本輪**不需改 `web/firestore.rules`**。

## 使用者決策（brainstorming 結論）

1. 區塊＝**收藏 ＋ 遊玩紀錄**（不含投稿）。
2. 形式＝**獨立頁面 `profile.html`**（由 build 產生，可加書籤、未來擴充基礎）。

## 架構總覽

```
build（easyrpg_web_build.build_library）
  ├─ menu.write_menu(...)     → index.html（加「👤 我的」連結到 profile.html）
  ├─ menu.write_profile(...)  → profile.html（嵌入 window.__GAMES、載入 account.js/profile.js/profile.css）
  └─ pwa.install_web_assets() → 自動複製 profile.js/profile.css 進 dist
profile.html
  └─ profile.js（module，import account.js）
        ├─ 讀 users/<uid>/favorites → 我的收藏（依 addedAt 新到舊）
        └─ 讀 users/<uid>/history  → 最近遊玩（依 lastPlayedAt 新到舊，顯示已遊玩時間）
        用嵌入的 window.__GAMES（slug→{label,cover}）渲染卡片（連到 play-<slug>.html）
```

## 元件設計

### `menu.py`：`write_profile(dist, app_label, entries, icon_rel=pwa.ICON_REL) -> Path`

- 以模組層級模板字串 `_PROFILE_PAGE` 產 `profile.html`，與 `_PAGE`（首頁）風格一致（深色、同字型、
  `__PWAHEAD__`/`__TITLE__` 由 `pwa.pwa_head`/app_label 填）。
- 嵌入遊戲清單：把 `entries` 轉成 `{ slug: { label, cover } }`（cover＝`cover_rel or icon_rel`）以
  `json.dumps(..., ensure_ascii=False)` 寫成 `<script>window.__GAMES=…;</script>`（label/cover 由 JSON
  字面值安全注入）。
- 結構（body）：
  - 頂列：`<a href="index.html">← 返回遊戲庫</a>`、標題「我的」、登入狀態容器 `#me-auth`。
  - 兩區塊：`<section><h2>我的收藏</h2><div id="my-favs"></div></section>` 與
    `<section><h2>最近遊玩</h2><div id="my-history"></div></section>`。
- `<head>` 載入 `<link rel="stylesheet" href="profile.css">`；`</body>` 前
  `<script type="module" src="profile.js"></script>`。
- 回傳 `dist/profile.html` 路徑。

### `menu.py`：`write_menu` 加「我的」連結

- 在首頁工具列（`<div class="toolbar">…</div>`）內加 `<a href="profile.html" id="me-link">👤 我的</a>`
  （樣式與 `#clear`/`#favonly` 一致，放 favorites.css 或 menu.py 的 `<style>`）。

### `easyrpg_web_build.py`

- `menu.write_menu(...)` 之後加一行 `menu.write_profile(out, app_label, entries, icon_rel)`。

### `web/profile.js`（ES module，`import account.js`）

- `import { db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser } from './account.js';`
- `import { collection, getDocs, query, orderBy } from '…/firebase-firestore.js';`
- 讀 `const GAMES = window.__GAMES || {};`
- 後端未設定（`!isReady()`）→ 兩區塊顯示「站長尚未設定後端」，return。
- 登入狀態（`onAuthChange`）：更新 `#me-auth`（未登入「用 Google 登入」；已登入名字＋登出）；
  未登入時兩區塊顯示「登入後可看你的收藏與遊玩紀錄」；登入時 `loadFavs()`＋`loadHistory()`。
- `loadFavs()`：`getDocs(query(collection(db,'users',uid,'favorites'), orderBy('addedAt','desc')))`
  → 對每個 doc.id（slug）查 `GAMES[slug]`，有才渲染卡片（封面＋名稱＋連結 `play-<slug>.html`）；
  空 → 「還沒有收藏」。
- `loadHistory()`：`getDocs(query(collection(db,'users',uid,'history'), orderBy('lastPlayedAt','desc')))`
  → 卡片＋「已遊玩 Xh Ym」（小工具 `fmt(totalSeconds)`）；查不到 `GAMES[slug]` 略過；空 → 「還沒有遊玩紀錄」。
- 卡片以 `textContent` 放名稱（無 XSS 疑慮）、`img` 放封面。

### `web/profile.css`

頂列、區塊標題、卡片網格（沿用首頁卡片風格）、「已遊玩」小標樣式；深色與站一致。

## 資料流

1. 開 profile.html → account.js 初始化 Firebase、`onAuthChange`。
2. 未登入：頂列顯示登入鈕，區塊提示登入。
3. 登入：各讀一次 `users/<uid>/favorites`、`users/<uid>/history`（各一次 getDocs）→ 用 `window.__GAMES` 渲染。

## 錯誤處理

- `isReady` false → 區塊顯示「站長尚未設定後端」。
- 讀取失敗（網路/規則）→ 該區塊顯示「載入失敗，請稍後再試」。
- 收藏/紀錄對應的遊戲已不在 `__GAMES`（下架）→ 略過該筆，不報錯。
- 空清單 → 友善提示。

## 測試

- **Python（自動）**：
  - `menu.write_profile` 產出 `profile.html`，含 `window.__GAMES`（含某 slug/label）、`#my-favs`、
    `#my-history`、`profile.css`/`profile.js` 引用、`返回` 連結。
  - `menu.write_menu` 首頁含 `id="me-link"` 且 `href="profile.html"`。
  - `pwa.install_web_assets` 複製 `profile.js`/`profile.css` 進 dist。
- **JS 語法**：`node --check`（`profile.js`）。
- **前端/互動（手動）**：登入→個人頁顯示我的收藏與最近遊玩（封面/名稱/已遊玩時間）、點卡片進遊戲、
  未登入只顯示提示、另一帳號看到自己的資料。

## 非目標（YAGNI）

- 我的投稿（需 collectionGroup 查詢＋Firestore 索引；後續輪次）。
- 公開個人頁給別人看、頭像上傳、編輯個人資料。
- 收藏/紀錄的排序選項、分頁、限筆數。
- 從遊戲頁進個人頁（本輪入口只在首頁；之後要再加）。

## 前置依賴

收藏與遊玩紀錄規則已允許本人讀取，**本輪不需改規則**。站長重建部署即可（規則不必重發，除非
之前未發布收藏/紀錄規則）。
