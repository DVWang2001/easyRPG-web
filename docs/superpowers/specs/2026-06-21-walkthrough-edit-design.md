# 設計：作者編輯攻略

日期：2026-06-21

## Context

攻略投稿功能（見 `2026-06-21-walkthroughs-foundation-design.md`）目前只支援**新增**與**刪除**，
規則明確禁止更新（`allow update: if false`）。使用者希望讓**作者本人**能編輯自己已投稿的攻略
（修正錯字、補內容）。管理員維持「可刪、但不改別人的」。這是對既有攻略功能的小幅擴充，
動到 `web/firestore.rules` 與 `web/walkthrough.js` 兩個檔。

## 決策（brainstorming 結論）

- 編輯權限：**只有作者本人**（不含管理員）。刪除維持「作者或管理員」不變。

## 元件設計

### Firestore 規則（`web/firestore.rules`）

把 `allow update: if false;` 改成只有原作者能更新，並守住不可竄改欄位：

```
allow update: if request.auth != null
  && resource.data.authorUid == request.auth.uid                 // 只有原作者
  && request.resource.data.authorUid == resource.data.authorUid  // 不可改作者
  && request.resource.data.createdAt == resource.data.createdAt  // 不可改建立時間
  && request.resource.data.title is string
  && request.resource.data.title.size() > 0
  && request.resource.data.title.size() <= 200
  && request.resource.data.html is string
  && request.resource.data.html.size() <= 50000
  && request.resource.data.keys().hasOnly(
       ['title','html','authorName','authorUid','createdAt','updatedAt']);
```

（`firebase-config.js`/規則內的 `YOUR_ADMIN_UID` 等佔位符不受影響；`.example` 範本不需改。）

### 面板邏輯（`web/walkthrough.js`）

- **狀態**：模組層級加一個 `editingId`（null＝新投稿；非 null＝正在編輯該 id）。
- **每篇攻略操作區**（`renderItem`）：
  - 「**編輯**」鈕：**只給作者本人**（`u && u.uid === data.authorUid`）。
  - 「刪除」鈕：維持「作者或管理員」（`u && (u.uid === data.authorUid || isAdmin(u.uid))`）。
  - 點「編輯」→ 開啟既有 Quill 編輯器（`openEditor()`）→ 預填 `titleEl.value = data.title`、
    用 Quill 正規做法填內文 `quill.clipboard.dangerouslyPasteHTML(data.html)` → 設 `editingId = id`
    → 送出鈕文字改「更新」。
- **送出**（`.wt-submit`）：
  - 若 `editingId` → `updateDoc(doc(db,'games',WT.slug,'walkthroughs',editingId),
    { title, html, updatedAt: serverTimestamp() })`（只送變動欄位，`authorUid`/`createdAt`
    自然不變，規則才放行）。
  - 否則維持原本 `addDoc`（新投稿，含 `createdAt`）。
  - 成功後：`editingId = null`、清空表單、隱藏編輯器、送出鈕文字還原「送出」、`loadList()`。
- **重置編輯狀態**：點「＋ 投稿攻略」與「取消」時 `editingId = null`、清空標題與內文、送出鈕還原
  「送出」，避免新投稿誤帶舊內容。
- **已編輯標記**：`renderItem` 若 `data.updatedAt` 存在 → 標題列加「（已編輯）」小標。

### 第三方／既有

沿用既有 Quill 編輯器、`account.js`（`currentUser`/`isAdmin`）、`firebase-firestore` 的
`updateDoc`/`doc`（`updateDoc` 需新 import）、DOMPurify 顯示。

## 資料流

開面板讀清單（不變）→ 作者點某篇「編輯」→ 編輯器預填 → 改完按「更新」→ `updateDoc` →
重查清單，該篇顯示新內容＋「（已編輯）」。

## 錯誤處理

- 更新失敗（網路／規則拒絕）→ `alert('更新失敗，請稍後再試')`，不清空編輯中的內容。
- 同投稿一樣的前端長度檢查（標題 1–200、內文位元組 ≤50000）。
- 顯示沿用 `DOMPurify.sanitize`（不變）。

## 測試

- **`walkthrough.js`**：`node --check` 語法檢查（瀏覽器/Firestore 互動無法 pytest）。
- **規則**：Firestore 規則模擬器或手動驗——作者能改自己的；改不了別人的；改不動
  `authorUid`/`createdAt`；未登入不能改。
- 注入/資產複製那塊不變，無需新 Python 測試。

## 非目標（YAGNI）

- 管理員編輯別人的攻略（本輪只作者本人）。
- 編輯歷史/版本控制、草稿。

## 前置依賴

要實際運作，需先解掉目前「載入失敗」（Firestore 規則未發布／資料庫權限）——否則讀寫都被擋。
