# 設計：每遊戲留言 ＋ 五星評分（Phase 1 補齊）

日期：2026-06-21

## Context

社群地基（`2026-06-21-walkthroughs-foundation-design.md`）已完成 Phase 0（Google 登入＋
Firebase＋管理員）與 Phase 1 的「攻略投稿/編輯/刪除」。本輪補齊 Phase 1 剩餘的兩塊：
**每遊戲留言** 與 **五星評分**。兩者都疊在既有地基上（`import account.js`），與攻略並列為
「每遊戲社群」內容。

完整藍圖見 foundation spec；本輪只做留言＋評分，後續 Phase 2–4（收藏/個人頁/雲端存檔/
熱度/站務）各為獨立輪次。

## 使用者決策（brainstorming 結論）

1. 評分＝**五星評分**（非單純按讚）：一人一票、可改、可收回；顯示平均分＋人數。
2. 留言＝**平鋪單層**（不巢狀回覆）。
3. UI 入口＝**新增「留言」鈕**（與「攻略」並排於左上 `#saveui`），開獨立面板；評分放面板頂、
   留言放面板下。
4. 留言內容＝**純文字**（不富文字、不貼圖）。
5. 對齊攻略慣例：公開可讀、登入才能寫、立即公開、作者或管理員可刪。留言**不做編輯**（短，YAGNI）。

## 架構總覽

```
遊戲頁 play-<slug>.html（左上 #saveui）
  ├─ 「攻略」鈕 → walkthrough.js（既有）
  └─ 「留言」鈕 → community.js（本輪新增）
        ├─ import account.js（地基：db / 登入 / currentUser / isAdmin）
        ├─ 評分：讀/寫 games/<slug>/ratings/<uid>（doc id = uid）
        └─ 留言：讀/寫 games/<slug>/comments/<自動id>
Firestore
  ├─ games/<slug>/comments/<id>  { text, authorName, authorUid, createdAt }
  └─ games/<slug>/ratings/<uid>  { stars, authorUid, updatedAt }
```

## 元件設計

### `web/community.js`（ES module，新增）

- 讀頁面注入的 `window.__WT = { slug, title }`（沿用攻略既有注入，不另設變數）。
- 綁定左上角「留言」鈕（`#cm-open`）→ 開/關面板。
- 面板 DOM（仿 `walkthrough.js`：`#cm-panel` ＝ `.cm-backdrop` ＋ `.cm-dialog`，✕ 與點遮罩關閉）：
  - **標題列**：遊戲名 ＋ 登入狀態（未登入「用 Google 登入」；已登入名字＋登出）＋ ✕。
  - **評分區**（頂部）：
    - 平均分顯示：`★ x.x · N 人`（x.x 取一位小數；N=0 時顯示「尚無評分」）。
    - 「你的評分」：1–5 顆可點的星（登入才可點）。點第 k 星 → 寫 `stars=k`；
      **再點目前已選的同一顆星 → 收回**（刪除自己的 rating 文件）。
    - 開面板時一次性 `getDocs(games/<slug>/ratings)` → 算平均（sum/count，一位小數）＋人數，
      並標出 `currentUser()` 自己的分（doc id === uid）。
  - **留言區**（下方）：
    - 列表：一次性 `getDocs` `games/<slug>/comments` 依 `createdAt` 由新到舊；
      投稿/刪除後重查一次更新。
    - 每則：內容（`textContent` ＋ `white-space:pre-wrap` 保留換行）、作者名、日期；
      作者本人或管理員顯示「刪除」（`deleteDoc`，規則把關）。
    - 輸入：`<textarea maxlength="500">` ＋「送出」。未登入→引導 `signInWithGoogle()`；
      已登入→`addDoc({ text, authorName: displayName||'匿名', authorUid: uid, createdAt: serverTimestamp() })`。
    - 送出前端檢查：去頭尾空白後非空、長度 1–500；不符則提示不送出。
- **暫停整合**：`openPanel()` → `window.__epPause(true,'cm')`；`closePanel()` →
  `window.__epPause(false,'cm')`（沿用 pwa 注入的假暫停 helper：靜音＋擋輸入；helper 不存在則 guard 略過）。
- **顯示安全**：留言一律以 `textContent` 寫入（不碰 innerHTML）→ 純文字無 XSS，不需 DOMPurify。

### `web/community.css`（新增）

面板與按鈕樣式（深色、與站一致；置中浮層＋背景遮罩），與 `walkthrough.css` 風格一致但
class 前綴用 `cm-` 避免衝突；星星可點樣式（hover/selected）。

### `web/firestore.rules`（擴充既有檔）

在現有 `match /games/{slug}/...` 內，於 `walkthroughs` 規則旁新增：

```
// 留言：公開可讀；登入才能建立（作者＝本人、純文字 1–500）；刪除＝作者本人或管理員；不可改。
match /comments/{id} {
  allow read: if true;
  allow create: if request.auth != null
    && request.resource.data.authorUid == request.auth.uid
    && request.resource.data.text is string
    && request.resource.data.text.size() > 0
    && request.resource.data.text.size() <= 500
    && request.resource.data.keys().hasOnly(['text','authorName','authorUid','createdAt']);
  allow update: if false;
  allow delete: if request.auth != null
    && (resource.data.authorUid == request.auth.uid
        || request.auth.uid == 'YOUR_ADMIN_UID');
}
// 評分：公開可讀；一人一票（doc id = uid）；建立/更新需本人且 1–5 整數；刪除＝本人或管理員。
match /ratings/{uid} {
  allow read: if true;
  allow create, update: if request.auth != null
    && uid == request.auth.uid
    && request.resource.data.authorUid == request.auth.uid
    && request.resource.data.stars is number
    && request.resource.data.stars >= 1
    && request.resource.data.stars <= 5
    && request.resource.data.keys().hasOnly(['stars','authorUid','updatedAt']);
  allow delete: if request.auth != null
    && (uid == request.auth.uid || request.auth.uid == 'YOUR_ADMIN_UID');
}
```

（`YOUR_ADMIN_UID` 沿用攻略規則的同一佔位符，由站長換成自己的 uid；`.example` 範本不受影響。）

### `pwa.py`（注入＋資產複製）

- `install_web_assets`：把 `community.js`、`community.css` 一起複製進 `dist/`（沿用既有清單，
  跳過 `*.example.js` 的規則不變）。
- `write_game_pages`：每頁在現有 `#saveui` 內、`攻略` 鈕之後加入「留言」鈕（`id="cm-open"`）；
  加入 `<link rel="stylesheet" href="community.css">` 與
  `<script type="module" src="community.js"></script>`。`window.__WT` 已存在，不重覆注入。

## 資料流

1. 開遊戲頁 → `account.js` 初始化 Firebase、`onAuthChange` 更新登入狀態。
2. 點「留言」→ 面板開啟＋`__epPause(true,'cm')` → 讀 ratings（算平均＋自己的分）與 comments（渲染列表）。
3. 評分：點第 k 星 → `setDoc(ratings/<uid>, {stars:k, authorUid:uid, updatedAt})`；點已選同星 →
   `deleteDoc(ratings/<uid>)`。完成後重算平均。
4. 留言：未登入→`signInWithGoogle()`；已登入→`addDoc` 寫入→重查列表。
5. 刪除留言：作者或管理員→`deleteDoc`（規則把關）。
6. 關面板 → `__epPause(false,'cm')`。

## 錯誤處理

- `firebase-config.js` 未設定（仍佔位符）→「留言」面板顯示「站長尚未設定後端」，不丟未捕捉錯誤
  （沿用攻略的 `isReady()` 檢查）。
- 網路/Firestore 失敗（讀/寫/評分）→ 面板顯示友善訊息，可重試（評分失敗 alert、不改 UI 狀態）。
- 送出驗證：空白/超長留言、未登入→前端擋下並提示。
- 平均分讀取：人少直接讀整個 ratings 子集合算（YAGNI，不維護計數器）。

## 測試

- **Python（自動）**：
  - `pwa.write_game_pages` 注入「留言」鈕（`cm-open`）、`community.css`/`community.js` 引用。
  - `pwa.install_web_assets` 把 `community.js`/`community.css` 複製進 `dist/`。
- **JS 語法**：`node --check`（`community.js` 無瀏覽器/Firestore 端可自動測）。
- **前端/規則（手動）**：登入→評分（一人一票、可改、再點同星收回）→平均分正確；留言（立即公開、
  另裝置/無痕看得到）→作者/管理員可刪、未登入只能看；規則模擬器驗未登入不能寫、非本人不能改別人評分。

## 非目標（YAGNI）

- 留言編輯、巢狀回覆、留言貼圖/富文字、自動把網址變連結。
- 維護式平均分聚合（計數器/Cloud Function）；人多再議。
- 評分與留言綁在同一筆。
- 全域帳號列（沿用攻略：登入只在面板內觸發）。

## 前置依賴

與攻略相同：需站長已設好 Firebase 並**發布 Firestore 規則**（本輪規則為擴充，須一併重新發布），
否則讀寫被擋。
