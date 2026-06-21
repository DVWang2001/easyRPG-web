# 作者編輯攻略 ＋ 面板暫停遊戲 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓作者能編輯自己投稿的攻略；並在開啟存檔/攻略面板時暫停 EasyRPG 遊戲。

**Architecture:** 兩個小功能、動三個檔：Firestore 規則放行「作者更新」；`web/walkthrough.js` 加「編輯」鈕＋editingId 狀態（送出走 updateDoc）並在面板開/關時暫停/恢復；`pwa.py` 的 `_SAVE_UI` 內嵌 JS 定義 `window.__epPause`（呼叫 emscripten 的 pauseMainLoop/resumeMainLoop）並在導出/導入時暫停。

**Tech Stack:** Firebase Firestore 規則、Quill、Firestore JS SDK 9.23.0（`updateDoc`）、emscripten `pauseMainLoop`/`resumeMainLoop`；Python（pwa 注入）、pytest、node（JS 語法檢查）。

## Global Constraints

- **編輯權限**：只有作者本人（`u.uid === data.authorUid`）。刪除維持「作者或管理員」不變。
- **update 規則**：原作者；不可改 `authorUid`、不可改 `createdAt`；`title` 1–200、`html` ≤50000；
  欄位白名單 `['title','html','authorName','authorUid','createdAt','updatedAt']`。
- 編輯送出用 `updateDoc(..., { title, html, updatedAt: serverTimestamp() })`；新投稿維持 `addDoc`。
- 有 `updatedAt` 的攻略，清單標題列加「（已編輯）」。
- **暫停**：`window.__epPause(on)` 計數器（定義於先載入的 `_SAVE_UI` 內嵌 JS）；0→1 呼叫
  `easyrpgPlayer.pauseMainLoop()`、1→0 呼叫 `resumeMainLoop()`，皆先檢查 `easyrpgPlayer` 與方法存在。
- 攻略面板 open→暫停、close→恢復；導出前後 pause/resume（瞬間、無感）；導入按下→暫停、
  視窗重新取得焦點→恢復（取消檔案視窗也恢復；選了檔會 reload 不影響）。
- JS 改完跑 `cp web/X.js _check.mjs && node --check _check.mjs && rm _check.mjs`（無輸出＝OK）。
- pytest 在 repo 根目錄：`python -m pytest <path> -v`。

---

### Task 1: Firestore 規則放行「作者更新」

**Files:**
- Modify: `web/firestore.rules`

- [ ] **Step 1: 改規則**

把 `web/firestore.rules` 的這段註解與 `allow update: if false;`：

```
    // 攻略：公開可讀；登入才能建立（且作者＝本人、標題/內文長度受限）；
    // 刪除＝作者本人或管理員；不允許修改。
```
…（下略 create/delete 不動）…
```
      allow update: if false;
```

改成（註解更新 ＋ 作者更新規則）：

```
    // 攻略：公開可讀；登入才能建立（作者＝本人、長度受限）；
    // 刪除＝作者本人或管理員；更新＝只有原作者（不可改 authorUid/createdAt）。
```
```
      allow update: if request.auth != null
        && resource.data.authorUid == request.auth.uid
        && request.resource.data.authorUid == resource.data.authorUid
        && request.resource.data.createdAt == resource.data.createdAt
        && request.resource.data.title is string
        && request.resource.data.title.size() > 0
        && request.resource.data.title.size() <= 200
        && request.resource.data.html is string
        && request.resource.data.html.size() <= 50000
        && request.resource.data.keys().hasOnly(
             ['title','html','authorName','authorUid','createdAt','updatedAt']);
```

（只改註解與 `allow update` 那行；`allow read/create/delete` 維持原樣。）

- [ ] **Step 2: 確認檔案合理（無自動測試；規則正式驗證在 Firestore 規則模擬器/手動）**

Run: `grep -n "allow update" web/firestore.rules`
Expected: 顯示新的多行 `allow update: if request.auth != null ...`（不再是 `if false`）。

- [ ] **Step 3: Commit**

```bash
git add web/firestore.rules
git commit -m "feat(rules): 攻略允許作者本人更新（不可改 authorUid/createdAt）"
```

---

### Task 2: 存檔內嵌 JS 定義 `window.__epPause` 並暫停導出/導入

**Files:**
- Modify: `pwa.py`（`_SAVE_UI` 內嵌 JS）
- Test: `tests/test_pwa_gamepages.py`

**Interfaces:**
- Produces: 遊戲頁上 `window.__epPause(on:boolean)`（計數器；0→1 暫停遊戲、1→0 恢復），
  供攻略面板（Task 3）共用。

- [ ] **Step 1: 寫失敗測試**

在 `tests/test_pwa_gamepages.py` 末尾加：

```python
def test_write_game_pages_injects_pause_helper(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    pwa.write_game_pages(dist, [{"label": "甲", "slug": "g", "cover_rel": None}])
    html = (dist / "play-g.html").read_text(encoding="utf-8")
    # 共用暫停 helper 與 emscripten 暫停/恢復呼叫
    assert "window.__epPause" in html
    assert "pauseMainLoop" in html and "resumeMainLoop" in html
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_gamepages.py::test_write_game_pages_injects_pause_helper -v`
Expected: FAIL（尚無 `window.__epPause`）。

- [ ] **Step 3: 在 `_SAVE_UI` 的 IIFE 開頭定義 helper**

`pwa.py` 的 `_SAVE_UI` 裡，把：

```javascript
<script>(function(){
var SLUG=__SLUG__;
```

改成（加入暫停 helper）：

```javascript
<script>(function(){
var SLUG=__SLUG__;
window.__epPause=window.__epPause||(function(){var n=0;
function P(){try{var p=(typeof easyrpgPlayer!=="undefined")&&easyrpgPlayer;if(p&&typeof p.pauseMainLoop==="function")p.pauseMainLoop();}catch(e){}}
function R(){try{var p=(typeof easyrpgPlayer!=="undefined")&&easyrpgPlayer;if(p&&typeof p.resumeMainLoop==="function")p.resumeMainLoop();}catch(e){}}
return function(on){if(on){if(++n===1)P();}else{if(n>0&&--n===0)R();}};})();
```

- [ ] **Step 4: 導出時暫停（try/finally 保證恢復）**

把現有的 `saveexp` 點擊處理：

```javascript
document.getElementById("saveexp").onclick=function(){var m=mod();if(!m){alert("遊戲尚未載入完成，請稍候");return;}
var files=readSaves();if(!files.length){alert("找不到存檔（請先在遊戲裡存檔）");return;}
var blob=new Blob([makeZip(files)],{type:"application/zip"});
var a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=SLUG+"-saves.zip";a.click();
setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},1000);};
```

改成（整段包進 `__epPause(true)` … `finally __epPause(false)`）：

```javascript
document.getElementById("saveexp").onclick=function(){window.__epPause(true);try{
var m=mod();if(!m){alert("遊戲尚未載入完成，請稍候");return;}
var files=readSaves();if(!files.length){alert("找不到存檔（請先在遊戲裡存檔）");return;}
var blob=new Blob([makeZip(files)],{type:"application/zip"});
var a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=SLUG+"-saves.zip";a.click();
setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},1000);
}finally{window.__epPause(false);}};
```

- [ ] **Step 5: 導入時暫停（按下→暫停；焦點回來→恢復）**

把現有的 `saveimp` 點擊處理：

```javascript
document.getElementById("saveimp").onclick=function(){if(!mod()){alert("遊戲尚未載入完成，請稍候");return;}inp.click();};
```

改成：

```javascript
document.getElementById("saveimp").onclick=function(){if(!mod()){alert("遊戲尚未載入完成，請稍候");return;}
window.__epPause(true);
function onFocus(){window.removeEventListener("focus",onFocus);setTimeout(function(){window.__epPause(false);},300);}
window.addEventListener("focus",onFocus);
inp.click();};
```

（選了檔會走 `inp.onchange` 寫入後 `location.reload()`——遊戲重載，暫停狀態自然消失；取消檔案視窗則靠 `onFocus` 恢復。`inp.onchange` 不需改。）

- [ ] **Step 6: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_gamepages.py -v`
Expected: PASS（含新測試與既有存檔 UI 測試）。

- [ ] **Step 7: 全測試**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS。

- [ ] **Step 8: Commit**

```bash
git add pwa.py tests/test_pwa_gamepages.py
git commit -m "feat(pwa): window.__epPause 共用暫停＋導出/導入時暫停遊戲"
```

---

### Task 3: walkthrough.js 加作者編輯 ＋ 面板暫停

**Files:**
- Modify: `web/walkthrough.js`

**Interfaces:**
- Consumes: `window.__epPause`（Task 2，遊戲頁全域；不存在時 guard 略過）、Firestore `updateDoc`。

- [ ] **Step 1: 匯入 updateDoc**

把 `web/walkthrough.js` 第 2–4 行的 firestore import：

```javascript
import {
  collection, addDoc, getDocs, deleteDoc, doc, query, orderBy, serverTimestamp,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
```

改成（加 `updateDoc`）：

```javascript
import {
  collection, addDoc, getDocs, deleteDoc, doc, query, orderBy, serverTimestamp, updateDoc,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
```

- [ ] **Step 2: 加 editingId 狀態 ＋ submit 鈕參照**

把：

```javascript
const WT = window.__WT || { slug: '', title: '' };
let quill = null;
```

改成：

```javascript
const WT = window.__WT || { slug: '', title: '' };
let quill = null;
let editingId = null;   // null＝新投稿；非 null＝正在編輯的攻略 id
```

並在元素參照那段（`const titleEl = ...` 之後）加一行：

```javascript
const submitBtn = panel.querySelector('.wt-submit');
```

- [ ] **Step 3: 面板開/關時暫停/恢復遊戲**

把：

```javascript
function openPanel() { panel.hidden = false; loadList(); }
function closePanel() { panel.hidden = true; }
```

改成：

```javascript
function openPanel() {
  panel.hidden = false;
  if (window.__epPause) window.__epPause(true);
  loadList();
}
function closePanel() {
  panel.hidden = true;
  if (window.__epPause) window.__epPause(false);
}
```

- [ ] **Step 4: 清單顯示「（已編輯）」＋ 作者「編輯」鈕**

把 `renderItem` 的 summary 文字與作者/管理員操作區（目前只有刪除）：

```javascript
  sum.textContent = (data.title || '(無標題)') + ' — '
    + (data.authorName || '匿名') + ' ' + date;
  item.appendChild(sum);
```
…（body 那段不變）…
```javascript
  const u = currentUser();
  if (u && (u.uid === data.authorUid || isAdmin(u.uid))) {
    const del = document.createElement('button');
    del.type = 'button'; del.className = 'wt-del'; del.textContent = '刪除';
    del.onclick = async () => {
      if (!confirm('確定刪除這篇攻略？')) return;
      try {
        await deleteDoc(doc(db, 'games', WT.slug, 'walkthroughs', id));
        loadList();
      } catch (e) { alert('刪除失敗'); }
    };
    item.appendChild(del);
  }
  return item;
```

改成（summary 加「（已編輯）」；先放作者專屬「編輯」鈕，再放原刪除鈕）：

```javascript
  sum.textContent = (data.title || '(無標題)') + ' — '
    + (data.authorName || '匿名') + ' ' + date
    + (data.updatedAt ? '（已編輯）' : '');
  item.appendChild(sum);
```
…（body 那段不變）…
```javascript
  const u = currentUser();
  if (u && u.uid === data.authorUid) {       // 只有作者本人能編輯
    const ed = document.createElement('button');
    ed.type = 'button'; ed.className = 'wt-edit'; ed.textContent = '編輯';
    ed.onclick = () => startEdit(id, data);
    item.appendChild(ed);
  }
  if (u && (u.uid === data.authorUid || isAdmin(u.uid))) {   // 作者或管理員能刪除
    const del = document.createElement('button');
    del.type = 'button'; del.className = 'wt-del'; del.textContent = '刪除';
    del.onclick = async () => {
      if (!confirm('確定刪除這篇攻略？')) return;
      try {
        await deleteDoc(doc(db, 'games', WT.slug, 'walkthroughs', id));
        loadList();
      } catch (e) { alert('刪除失敗'); }
    };
    item.appendChild(del);
  }
  return item;
```

- [ ] **Step 5: 加 startEdit；改寫 新投稿/取消/送出 以支援編輯模式**

把目前的 `.wt-new`、`.wt-cancel`、`.wt-submit` 三個處理（第 188–217 行）整段：

```javascript
panel.querySelector('.wt-new').onclick = () => {
  if (!currentUser()) { signInWithGoogle().then(openEditor).catch(() => alert('登入失敗')); return; }
  openEditor();
};
panel.querySelector('.wt-cancel').onclick = () => {
  titleEl.value = '';
  if (quill) quill.setText('');
  editorEl.hidden = true;
};
panel.querySelector('.wt-submit').onclick = async () => {
  const u = currentUser();
  if (!u) { alert('請先登入'); return; }
  const title = titleEl.value.trim();
  const html = quill ? quill.root.innerHTML : '';
  if (!title) { alert('請輸入標題'); return; }
  if (title.length > 200) { alert('標題過長（上限 200 字）'); return; }
  if (new Blob([html]).size > 50000) { alert('內文過長（請精簡或減少圖片數量）'); return; }
  try {
    await addDoc(collection(db, 'games', WT.slug, 'walkthroughs'), {
      title, html,
      authorName: u.displayName || '匿名',
      authorUid: u.uid,
      createdAt: serverTimestamp(),
    });
    titleEl.value = '';
    if (quill) quill.setText('');
    editorEl.hidden = true;
    loadList();
  } catch (e) { alert('投稿失敗，請稍後再試'); }
};
```

改成：

```javascript
function resetEditor() {
  editingId = null;
  titleEl.value = '';
  if (quill) quill.setText('');
  submitBtn.textContent = '送出';
  editorEl.hidden = true;
}
function startEdit(id, data) {
  openEditor();                  // 確保 quill 已建立
  editingId = id;
  titleEl.value = data.title || '';
  quill.clipboard.dangerouslyPasteHTML(data.html || '');
  submitBtn.textContent = '更新';
}
panel.querySelector('.wt-new').onclick = () => {
  const go = () => { openEditor(); editingId = null; titleEl.value = ''; quill.setText(''); submitBtn.textContent = '送出'; };
  if (!currentUser()) { signInWithGoogle().then(go).catch(() => alert('登入失敗')); return; }
  go();
};
panel.querySelector('.wt-cancel').onclick = resetEditor;
panel.querySelector('.wt-submit').onclick = async () => {
  const u = currentUser();
  if (!u) { alert('請先登入'); return; }
  const title = titleEl.value.trim();
  const html = quill ? quill.root.innerHTML : '';
  if (!title) { alert('請輸入標題'); return; }
  if (title.length > 200) { alert('標題過長（上限 200 字）'); return; }
  if (new Blob([html]).size > 50000) { alert('內文過長（請精簡或減少圖片數量）'); return; }
  try {
    if (editingId) {
      await updateDoc(doc(db, 'games', WT.slug, 'walkthroughs', editingId), {
        title, html, updatedAt: serverTimestamp(),
      });
    } else {
      await addDoc(collection(db, 'games', WT.slug, 'walkthroughs'), {
        title, html,
        authorName: u.displayName || '匿名',
        authorUid: u.uid,
        createdAt: serverTimestamp(),
      });
    }
    resetEditor();
    loadList();
  } catch (e) { alert(editingId ? '更新失敗，請稍後再試' : '投稿失敗，請稍後再試'); }
};
```

（注意：`openEditor` 函式本身不變；它只負責 `editorEl.hidden=false` 與建立 quill。）

- [ ] **Step 6: 語法檢查**

Run: `cp web/walkthrough.js _check.mjs && node --check _check.mjs && rm _check.mjs`
Expected: 無輸出（語法正確）。

- [ ] **Step 7: Commit**

```bash
git add web/walkthrough.js
git commit -m "feat(web): 攻略加作者編輯（updateDoc/已編輯標記）＋面板開關時暫停遊戲"
```

---

## 收尾：手動驗證（非自動測試）

- [ ] 重建並部署（且 Firestore 規則已重新發布、後端可正常讀寫）。
- [ ] **編輯**：登入後對自己的攻略點「編輯」→ 編輯器預填原內容、送出鈕顯示「更新」→ 改完按更新
  → 清單顯示新內容＋「（已編輯）」；別人的攻略沒有「編輯」鈕（管理員也沒有，但仍可刪）。
- [ ] **暫停**：開「攻略」面板→遊戲畫面凍結、角色不動、按鍵無效；關閉面板→繼續。
- [ ] **導入暫停**：按「導入存檔」→遊戲暫停；取消檔案視窗→恢復；選檔→匯入後 reload。
- [ ] **導出**：瞬間下載（暫停無感）。

## Self-Review 註記（已檢查）

- **Spec 覆蓋**：編輯規則(Task1)、編輯 UI/updateDoc/已編輯標記/作者限定(Task3)、暫停 helper(Task2)、
  面板/導出/導入暫停(Task2+3) 皆有對應任務。
- **型別一致**：`window.__epPause(on)` 定義(Task2)與使用(Task3)一致；`editingId`/`submitBtn`/
  `startEdit`/`resetEditor` 在 Task3 內自洽；Firestore 欄位白名單與 updateDoc 送的欄位
  （title/html/updatedAt，未動 authorUid/createdAt）符合規則。
- **非自動測試**：Firestore 規則與 Quill/暫停互動屬瀏覽器端，靠收尾手動驗；Python 測試涵蓋暫停
  helper 注入。
