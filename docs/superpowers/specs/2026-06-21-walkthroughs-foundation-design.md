# 設計：社群地基 ＋ 攻略投稿（第一輪）

日期：2026-06-21

## Context（背景與目標）

easyRPG-web 目前是純靜態站（部署到 GitHub Pages），把 RPG Maker 遊戲打包成網頁。
使用者想把它擴充成「小遊戲入口網站」，要做社群內容、個人化、探索/熱度、站務多群功能。

完整藍圖（已與使用者確認）分階段：
- **Phase 0 地基**：Google 登入 ＋ Firebase 資料庫 ＋ 管理員身分（所有功能的共同基礎）。
- **Phase 1 每遊戲社群**：攻略投稿、留言、評分/按讚。
- **Phase 2 個人化**：收藏、遊玩紀錄、個人頁、雲端存檔同步。
- **Phase 3 探索/熱度**：瀏覽次數、熱門排行。（相似遊戲推薦：已取消，不做。）
- **Phase 4 站務**：公告、分享、檢舉、管理後台。
- 已知不可行：遊戲內排行榜（RPG Maker 遊戲不回報分數，無掛勾）。

**本規格只涵蓋第一輪：Phase 0 地基 ＋ 攻略投稿。** 地基刻意設計成可重用，之後每個
功能 import 同一套登入/資料庫即可疊上去。參考 `C:\opensource\workqueue`（Firebase
Firestore ＋ Google 登入 ＋ Quill 富文字 ＋ marked/DOMPurify）的設計。

## 使用者決策（brainstorming 結論）

1. 後端：**新建專用 Firebase 專案**（免費 Spark 方案足夠；config 由使用者填入）。
2. 投稿權限：**Google 登入即可投稿、立即公開**；閱讀公開不需登入；管理員（站長）可刪任意。
3. 入口：每個遊戲頁左上角一顆「**攻略**」鈕（和導出/導入存檔同排、全螢幕時一起隱藏），
   點開的面板**既可看也可投稿**。
4. 編輯器：**Quill 富文字**；存 HTML，顯示時 DOMPurify 消毒。
5. 圖片：可內嵌，但**自動上傳到免費圖床（免綁信用卡），HTML 只存回傳的圖片網址**（非 base64），
   讓 Firestore 文件維持很小。

## 架構總覽

```
瀏覽器（遊戲頁 play-<slug>.html）
  └─ 左上角「攻略」鈕（注入；同 #saveui 區、全螢幕隱藏）
        └─ walkthrough.js（ES module）
              ├─ import account.js（共用地基：Firebase init / Google 登入 / db）
              ├─ 讀 games/<slug>/walkthroughs（公開、即時或一次性查詢）
              ├─ 投稿（Quill → HTML → 寫入 Firestore）
              └─ 顯示（DOMPurify 消毒 HTML）
Firebase 專案（使用者新建）
  ├─ Authentication：Google 登入
  └─ Firestore：games/<slug>/walkthroughs/<id>
```

## 元件設計

### 地基（可重用）

- **`web/firebase-config.js`**：`export const firebaseConfig = {...}`，由使用者貼上新專案
  的 web config。Firebase web config 非機密（安全靠 Firestore 規則），可進版控。
  同檔也放圖床設定 `export const imageUpload = { provider:"imgur", clientId:"..." }`
  （由使用者填；同屬「使用者填自己的 key」的設定）。
- **`web/account.js`**（ES module，地基核心）：
  - 初始化 Firebase App、Auth、Firestore（用 gstatic CDN 的 firebase 9.x 模組）。
  - 匯出：`db`、`auth`、`currentUser()`、`signInWithGoogle()`、`signOut()`、
    `onAuthChange(cb)`、`isAdmin(uid)`、常數 `ADMIN_UID`。
  - `ADMIN_UID`：站長的 Google uid，常數寫在這（前端據此顯示管理操作；真正把關在規則）。
  - 設計成「之後留言/評分/收藏…都 import 這支」。
- **`web/firestore.rules`**：安全規則檔（artifact，使用者貼進 Firestore Console）。本輪內容：
  ```
  rules_version = '2';
  service cloud.firestore {
    match /databases/{database}/documents {
      match /games/{slug}/walkthroughs/{id} {
        allow read: if true;
        allow create: if request.auth != null
          && request.resource.data.authorUid == request.auth.uid
          && request.resource.data.title is string
          && request.resource.data.title.size() > 0
          && request.resource.data.title.size() <= 200
          && request.resource.data.html is string
          && request.resource.data.html.size() <= 50000;
        allow delete: if request.auth != null
          && (resource.data.authorUid == request.auth.uid
              || request.auth.uid == 'ADMIN_UID_PLACEHOLDER');
        allow update: if false;
      }
    }
  }
  ```
  （`ADMIN_UID_PLACEHOLDER` 由使用者換成自己的 uid。）

### 攻略功能

- **`web/walkthrough.js`**（ES module，`import` account.js）：
  - 讀頁面注入的設定 `window.__WT = { slug, title }`。
  - 綁定左上角「攻略」鈕 → 開/關面板。
  - 面板：
    - 標題列＝遊戲名 ＋ 關閉、登入狀態（未登入顯示「用 Google 登入」；已登入顯示名字/登出）。
    - 攻略清單：**面板開啟時一次性查詢**（`getDocs`，非即時監聽，省讀取額度）
      `games/<slug>/walkthroughs` 依 `createdAt` 由新到舊；投稿/刪除後重查一次更新。
      每筆顯示標題/作者/日期，點開渲染 `DOMPurify.sanitize(html)`；作者本人或管理員顯示「刪除」。
    - 「＋ 投稿攻略」：未登入→引導登入；已登入→Quill 編輯器（標題輸入 ＋ 內文）＋送出。
      送出寫入 `{ title, html, authorName, authorUid, createdAt: serverTimestamp() }`。
  - Quill 工具列：標題層級、粗體、斜體、清單（有序/無序）、連結、**圖片**。
  - **圖片自動上傳（自訂 Quill image handler）**：使用者選圖 → 不走 Quill 預設的 base64 內嵌，
    改成上傳到設定的免費圖床 → 取得網址 → 以該網址插入 `<img>`。上傳中顯示「上傳中…」、
    失敗顯示訊息且不影響其餘內容。圖床為**可設定**（避免綁死單一服務）：預設用 imgur 匿名
    上傳（需 Client-ID，放在設定檔；CORS 友善），實作時驗證 CORS/可用性，必要時換家
    （如 catbox.moe）。圖檔大小上限（如 ≤5 MB）前端先擋。
  - 送出前前端檢查長度（標題 1–200、內文 HTML ≤50,000；因圖片只存網址，文件維持很小）；
    後端規則再把關一次。
- **`web/walkthrough.css`**：面板與按鈕樣式（深色、與站一致；面板為置中浮層 ＋ 背景遮罩）。

### 第三方資源（CDN）

Quill 1.3.7、DOMPurify、Firebase 9.x（gstatic 模組）。投稿/讀取本來就要連網，故走 CDN；
不納入 service worker 離線快取。

## 建置整合

- **複製 web 資產**：新增 `pwa.install_web_assets(dist)`，把 `web/` 下的 `account.js`、
  `walkthrough.js`、`walkthrough.css`、`firebase-config.js` 複製進 `dist/`；由
  `easyrpg_web_build.build_library` 在產生遊戲頁前呼叫一次。
- **注入遊戲頁**：`pwa.write_game_pages` 對每頁加入：
  1. 左上角「攻略」鈕（放進既有 `#saveui` 容器，沿用其全螢幕隱藏）。
  2. `<script>window.__WT={slug:"<slug>",title:"<title>"}</script>`（slug/title 以 JSON 字面值安全注入）。
  3. `<link rel="stylesheet" href="walkthrough.css">` 與 `<script type="module" src="walkthrough.js"></script>`。
- service worker：js/css 屬「外殼」→ network-first（沿用現況，部署即更新）。

## 資料流

1. 開遊戲頁 → 注入的設定與 script 載入 → `account.js` 初始化 Firebase、`onAuthChange` 更新登入狀態。
2. 點「攻略」→ 面板開啟 → 查 `games/<slug>/walkthroughs` → 渲染清單（消毒 HTML）。
3. 投稿：未登入→`signInWithGoogle()`；已登入→填 Quill→送出→`addDoc` 寫入→清單即時/重查更新。
4. 刪除：作者或管理員→`deleteDoc`（規則把關）。

## 錯誤處理

- `firebase-config.js` 未填（仍是佔位符）→「攻略」面板顯示「站長尚未設定後端」，不報未捕捉錯誤。
- 網路/Firestore 失敗 → 面板顯示友善訊息，可重試。
- 投稿驗證：空標題/超長/過大圖檔 → 前端擋下並提示。
- 圖片上傳失敗（圖床無回應/超額/CORS）→ 提示「圖片上傳失敗，可改貼網址或稍後再試」，
  不影響其餘文字內容。
- XSS：**顯示任何使用者 HTML 一律 `DOMPurify.sanitize` 後才插入 DOM**（公開投稿必要防線）；
  允許 `<img>` 但只放行 `http(s)` 來源，移除事件屬性（如 onerror）。

## 測試

- **Python（可自動測）**：
  - `pwa.write_game_pages` 注入「攻略」鈕、`window.__WT`（含正確 slug/title）、`walkthrough.js`/
    `walkthrough.css` 引用。
  - 建置會把 `web/` 的資產複製進 `dist/`。
- **前端（手動，沿用 workqueue 驗證過的模式）**：登入 → 投稿（含插入圖片，確認圖片自動上傳、
  HTML 存的是網址而非 base64）→ 在另一裝置/無痕看到 → 刪除。
- Firebase 規則：可用 Firestore 規則模擬器或手動驗（未登入不能寫、非作者非管理員不能刪）。

## 已知風險

- **圖床第三方依賴**：免費圖床（imgur 等）可能改政策/限額/刪舊圖。故圖床做成可設定、可更換；
  圖片失效時攻略文字仍在。日後若要更穩可改 Firebase Storage（需 Blaze）。

## 非目標（YAGNI，本輪不做）

- 圖片改用 Firebase Storage（本輪用免費圖床；之後要更穩再議）。
- 投稿審核流程（本輪「立即公開」）。
- 留言、評分、收藏、雲端存檔、公告、檢舉、管理後台（各為後續輪次，疊在本地基上）。
- 編輯既有攻略（本輪只允許新增與刪除）。
- 全站登入小工具（本輪登入只在攻略面板內觸發；全域帳號列日後再加）。
