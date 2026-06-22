# 設計：遊玩次數 ＋ 熱門排行（Phase 3 第一個）

日期：2026-06-22

## Context

Phase 0–2 已完成（地基、社群、個人化）。Phase 3「探索/熱度」先做**熱門排行**（相似遊戲推薦暫緩）。
這是專案**第一個公開聚合資料**：遊玩次數人人可讀、開遊戲頁就 +1（前面所有資料都是本人私有）。

## 使用者決策（brainstorming 結論）

1. 先做**熱門排行**（含遊玩次數）；相似遊戲推薦本輪不做。
2. 顯示＝**卡片顯次數 ＋ 工具列「🔥 熱門」排序鈕**（按下依次數重排現有卡片）。
3. 計數**不需登入**（要讓所有玩家都算）；**不需防腳本灌水**（站長明確表示目前不需要）。
4. 計數去重：每瀏覽器每遊戲**每天一次**（localStorage 記當天日期，避免重整重複計）。

## 架構總覽

```
遊戲頁 play-<slug>.html（popular.js 計數）
  └─ 載入時若今天未計過 → setDoc(stats/<slug>, { plays: increment(1) }, {merge:true})，記 localStorage
首頁 index.html（popular.js 顯示/排序）
  ├─ getDocs(collection('stats')) → 每張卡片角落顯「▶ 次數」
  └─ 工具列「🔥 熱門」鈕 → 依 plays 由高到低重排 #grid 卡片（再按還原）
Firestore（公開）
  └─ stats/<slug>  { plays: number }   公開可讀；寫入限「plays 恰 +1、只有 plays 欄位」
```

## 元件設計

### 資料模型（Firestore）
- `stats/<slug>` = `{ plays: number }`（slug＝doc id）。

### `web/firestore.rules`（擴充）—— 本輪安全重點
在 `match /databases/{database}/documents` 內、與 `games`/`users` 同層新增：
```
// 遊玩次數：公開可讀；任何人可把 plays +1（無其他欄位），不需登入。不允許刪除。
match /stats/{slug} {
  allow read: if true;
  allow create: if request.resource.data.keys().hasOnly(['plays'])
    && request.resource.data.plays == 1;
  allow update: if request.resource.data.keys().hasOnly(['plays'])
    && request.resource.data.plays == resource.data.plays + 1;
}
```
規則把每次寫入限制成「plays +1、無其他欄位」。不需登入故仍可被反覆呼叫灌水——站長已表明目前
不需防刷（無 Cloud Functions 可做更嚴格控制）。

### `web/popular.js`（ES module，`import { db, isReady } from './account.js'`）
- `import { doc, collection, getDocs, setDoc, increment } from '…/firebase-firestore.js';`
- `!isReady()` → 直接 return（不計數、首頁隱藏「🔥 熱門」鈕）。
- **遊戲頁情境**（`window.__WT && window.__WT.slug`、且無 `#grid`）：
  - `key = 'ep-pl-' + slug`；今日字串 `new Date().toISOString().slice(0,10)`。
  - 若 `localStorage[key] !== today` → `setDoc(doc(db,'stats',slug), { plays: increment(1) }, { merge:true })`
    成功後 `localStorage[key] = today`（失敗安靜略過）。
- **首頁情境**（有 `#grid`）：
  - 收集卡片：`#grid .card`，slug 從 `href="play-<slug>.html"` 解析；記錄原始順序。
  - `getDocs(collection(db,'stats'))` → `plays[slug]`。次數 > 0 的卡片塞「▶ N」badge；無資料/0 不顯 badge（排序時視為 0）。
  - 工具列「🔥 熱門」鈕（`#hot`）：點擊切換 `active`；on＝依 `plays[slug]`（無→0）由高到低、同分維持原序，重新 append 進 `#grid`；off＝按原始順序 append 還原。
  - 與既有搜尋/標籤隱藏並存（`.card[hidden]` 仍隱藏，只是排序位置變動）。

### `web/popular.css`
卡片「▶ 次數」badge（角落小標）、`#hot` 鈕（與 `#favonly`/`#clear` 同風格）、`#hot.active` 樣式。

### `menu.py`（首頁）
- 工具列加 `<button id="hot">🔥 熱門</button>`（在 `#favonly` 之後）。
- `<head>` 載 `popular.css`、`</body>` 前載入 `popular.js`（module）。

### `pwa.py`（遊戲頁）
- 新增 `_POP_SNIPPET`：`<script type="module" src="popular.js"></script>`（計數用；不需 css），接到 `body_add`。
- `popular.js`/`popular.css` 由 `install_web_assets` 自動複製。

## 資料流
1. 開遊戲頁 → popular.js 今日未計過 → `stats/<slug>.plays += 1`。
2. 開首頁 → 讀整個 `stats` 一次 → 卡片顯次數 → 「🔥 熱門」可依次數重排。

## 錯誤處理
- `!isReady()` → 不計數、首頁隱藏 `#hot`、不顯次數。
- 計數寫入失敗 → 安靜略過（不記 localStorage，下次再試）。
- 首頁讀 stats 失敗 → 不顯次數、`#hot` 仍可點但排序皆 0（等同原序）。
- 卡片無對應 stats → 次數 0、排序排後。

## 測試
- **Python（自動）**：`menu.write_menu` 首頁含 `id="hot"`、`popular.css`/`popular.js` 引用；
  `pwa.write_game_pages` 遊戲頁含 `popular.js` 引用；`install_web_assets` 複製 `popular.js`/`popular.css`。
- **JS 語法**：`node --check`（`popular.js`）。
- **手動**：開幾個遊戲頁 → 首頁卡片次數增加、「🔥 熱門」依次數重排、再按還原；同瀏覽器當天重開不重複計；
  未設定後端→無次數、無熱門鈕。

## 非目標（YAGNI）
- 相似遊戲推薦（本輪暫緩）。
- 嚴格防刷／唯一訪客數／趨勢圖（需後端/Functions）。
- 熱門 Top N 獨立區塊（本輪用排序重用現有網格）。
- 按讚熱度（評分功能已另有）。

## 前置依賴
需站長已設好 Firebase 並**發布 Firestore 規則**（本輪規則為擴充，須一併重新發布）。
