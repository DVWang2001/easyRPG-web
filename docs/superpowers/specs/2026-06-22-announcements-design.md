# 公告（Phase 4 站務）設計 spec

## 背景

easyRPG-web 的擴充藍圖 Phase 4「站務」包含：公告、分享、檢舉、管理後台。
分享已完成。**本 spec 只涵蓋「公告」**——管理員張貼一則站務公告，所有訪客在
首頁頂部看到可關閉的橫幅。

地基沿用既有那套：Firebase Firestore ＋ Google 登入 ＋ `ADMIN_UID` 管理員身分
（`web/account.js` 的 `isAdmin()`），富文字沿用攻略那套 Quill ＋ DOMPurify。

## 目標 / 非目標

**目標**
- 管理員在首頁內嵌富文字編輯一則公告；所有訪客在首頁頂部看到橫幅。
- 橫幅顯示發布日期，編輯過則另顯示編輯日期。
- 訪客可關閉橫幅；公告一更新就重新跳出。

**非目標（YAGNI，要再加）**
- 公告歷史 / 多則列表、獨立公告頁。
- 作者顯示、Markdown。
- 一般訪客載入 Quill（只有管理員按「編輯」時才 lazy-load）。

## 資料模型

Firestore 單一固定文件 `announcements/current`：

```
{
  html: string,         // 富文字 HTML（≤ 50000 bytes）
  createdAt: Timestamp, // 首次發布時間，只寫一次
  updatedAt: Timestamp  // 每次存檔更新；首發時 == createdAt
}
```

無作者欄（只有管理員能寫，省）。固定 doc id `current`，原地編輯。

## Firestore 規則

在 `web/firestore.rules` 的 `match /databases/{database}/documents` 內新增
（沿用既有 `'YOUR_ADMIN_UID'` 佔位符慣例——站長部署規則時自行替換成真實 uid）：

```
// 公告：公開可讀；只有管理員能寫（單一固定 doc，原地編輯）。
match /announcements/current {
  allow read: if true;
  allow write: if request.auth != null
    && request.auth.uid == 'YOUR_ADMIN_UID'
    && request.resource.data.keys().hasOnly(['html','createdAt','updatedAt'])
    && request.resource.data.html is string
    && request.resource.data.html.size() <= 50000;
}
```

（merge 寫入後 `request.resource.data` 為合併後完整狀態，含既有 `createdAt`，
故 `hasOnly(['html','createdAt','updatedAt'])` 對「只送 html＋updatedAt 的編輯」
仍成立。）

## 前端模組

新增 `web/announce.js` ＋ `web/announce.css`，由 `pwa.install_web_assets`
自動複製進 dist（掃 `web/*.js`、`*.css`，無須改 build）。`announce.js` import
`web/account.js`（`db`、`isReady`、`onAuthChange`、`isAdmin`、`currentUser`）。

### 橫幅（所有訪客）

- 掛在首頁 `#announce` 容器（toolbar 上方）。
- 載入時一次性讀 `announcements/current`。
- 若 doc 存在、`html` 非空、且未被本機關閉 → 顯示橫幅：
  - 內容 = `DOMPurify.sanitize(html, { ALLOWED_URI_REGEXP: /^(?:https?|mailto):/i })`
    （沿用攻略的消毒設定；公開內容必經消毒）。
  - 日期列：`發布於 <createdAt 日期>`；若 `updatedAt` 日期 ≠ `createdAt` 日期，
    再加「· 編輯於 <updatedAt 日期>」（用 `toLocaleDateString()`；以毫秒比較是否相等）。
  - ✕ 關閉鈕。
- 關閉 → `localStorage['ann-dismissed'] = String(updatedAt.toMillis())`，隱藏橫幅。
- 顯示前先比對：若 `localStorage['ann-dismissed']` 等於目前 `updatedAt` 毫秒則不顯示
  （公告一更新 → 毫秒改變 → 重新跳出）。
- `isReady()` 為 false（站長未設後端）→ 整個橫幅靜默不顯示，不報錯。

### 編輯（僅管理員）

- `onAuthChange`：登入且 `isAdmin(uid)` → 橫幅顯示「✎ 編輯」鈕（公告為空時也要能進編輯以首發）。
- 按「編輯」→ lazy-load Quill（動態插入 `quill.min.js` ＋ `quill.snow.css`，只載一次），
  inline 開編輯器，沿用攻略 toolbar：`header[1,2,3]`、`bold/italic`、`list ordered/bullet`、
  `link`。**不含圖片**（公告用不到，省 imgbb handler）。
- 進編輯器時把現有 `html` 灌進 Quill（`quill.clipboard.dangerouslyPasteHTML`）。
- 存檔：
  - `html = quill.root.innerHTML`；若 `new Blob([html]).size > 50000` → alert 擋下。
  - `payload = { html, updatedAt: serverTimestamp() }`；若載入時 doc 沒有 `createdAt`
    （首發）→ 加 `payload.createdAt = serverTimestamp()`。
  - `setDoc(doc(db,'announcements','current'), payload, { merge:true })`。
  - 成功 → 重新讀並重繪橫幅。（updatedAt 已變，dismissed 旗標自然失效，連管理員自己也會重新看到。）
- 「清空並隱藏」：編輯器存入空白（trim 後無文字）→ 仍寫 `html:''`，橫幅對所有人隱藏。
- 失敗 → `alert('儲存失敗，請稍後再試')`。

## menu.py 改動

`_PAGE` 模板（首頁）：

- `<head>`：在現有 `<link ... popular.css>` 後加 `<link rel="stylesheet" href="announce.css">`，
  並加 DOMPurify CDN：
  `<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.8/dist/purify.min.js"></script>`
  （與攻略頁同版本；橫幅渲染需要，故所有訪客都載——約 20KB）。
- `<body>`：在 `<header>` 之後、`<div class="toolbar">` 之前，加 `<div id="announce" hidden></div>`。
- body 尾：在現有 `popular.js` module script 後加
  `<script type="module" src="announce.js"></script>`。

Quill 不在 menu.py 預載——由 announce.js 在管理員按「編輯」時才 lazy-load。

## 測試

`tests/`（pytest，沿用既有 menu 注入測試風格）：

- menu.py 產生的首頁 HTML 含 `announce.css`、`announce.js`、DOMPurify CDN。
- `<div id="announce"` 出現且位置在 `<div class="toolbar"` 之前（DOM 順序）。

announce.js 的 Firestore 互動沿用既有「不測前端 SDK 互動」慣例（留言/評分/收藏
模組皆未測），靠手動驗證。

## 手動驗證（收尾）

- 管理員登入首頁 → 出現「✎ 編輯」→ 寫入富文字 → 橫幅顯示，日期為「發布於 今天」。
- 再次編輯 → 橫幅顯示「發布於 … · 編輯於 …」。
- 一般訪客（無痕）→ 看到橫幅 → 關閉 → 重整不再出現；管理員再編輯後 → 重新跳出。
- 公告清空 → 所有人都不再看到橫幅。
- 站長未設後端（`isReady()` false）→ 首頁無橫幅、無 console 錯誤。
