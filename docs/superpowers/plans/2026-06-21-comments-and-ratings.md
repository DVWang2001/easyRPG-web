# 每遊戲留言＋五星評分 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在每個遊戲頁加「留言」鈕 → 開面板，頂部五星評分（一人一票、可改可收回、顯示平均），下方平鋪純文字留言（登入投稿、立即公開、作者/管理員可刪）。

**Architecture:** 疊在既有社群地基上。新增前端模組 `web/community.js` ＋ `web/community.css`（`import account.js`），由 `pwa.py` 注入每遊戲頁並複製進 `dist/`。資料存 Firestore `games/<slug>/comments/*` 與 `games/<slug>/ratings/<uid>`（doc id＝uid 天然保證一人一票），規則擴充 `web/firestore.rules`。

**Tech Stack:** Firebase 9.23.0（gstatic CDN 模組）、純前端 ES module、Python build pipeline（pwa.py）、pytest。

## Global Constraints

- 設計依據：`docs/superpowers/specs/2026-06-21-comments-and-ratings-design.md`。
- Firebase SDK 版本固定 `https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js`（與既有一致）。
- 留言純文字，顯示一律用 `textContent`（不碰 innerHTML）→ 無 XSS、不需 DOMPurify。
- 留言長度 1–500 字；評分為 1–5 的數字（規則用 `is number`＋範圍，不用 `is int`：Web SDK 數字以 double 存）。
- 面板開/關呼叫 `window.__epPause(true/false,'cm')`（沿用 pwa 注入的假暫停 helper；不存在則 guard 略過）。
- 權限：公開可讀；登入才能寫；留言刪除＝作者或管理員；留言不可編輯。評分建立/更新限本人、刪除＝本人或管理員。
- `web/firebase-config.js`（真實金鑰）維持 gitignored，永不 commit；只動 `firestore.rules`、`community.*`、`pwa.py`、測試。
- 規則內管理員佔位符沿用既有 `YOUR_ADMIN_UID`（與攻略同一個）。

---

### Task 1: Firestore 規則 — 留言＋評分

**Files:**
- Modify: `web/firestore.rules`

**Interfaces:**
- Produces: Firestore 對 `games/{slug}/comments/{id}` 與 `games/{slug}/ratings/{uid}` 的讀寫權限（前端 Task 2 據此讀寫）。

- [ ] **Step 1: 在現有 walkthroughs 規則之後、`/games/{slug}` 區塊內新增兩段 match**

打開 `web/firestore.rules`，找到 `match /games/{slug}/walkthroughs/{id} { ... }` 這個區塊的**結尾 `}`**（它仍在 `match /games/{slug}` 之內）。在它後面、同層加入：

```
      // 留言：公開可讀；登入才能建立（作者＝本人、純文字 1–500）；刪除＝作者或管理員；不可改。
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
      // 評分：公開可讀；一人一票（doc id＝uid）；建立/更新需本人且 1–5；刪除＝本人或管理員。
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

（只新增；既有 `walkthroughs` 規則與 `YOUR_ADMIN_UID` 不動。確認大括號層級：兩段 match 與 walkthroughs 同層，仍在 `match /games/{slug}` 內。）

- [ ] **Step 2: 確認檔案合理（無自動測試；正式驗證在 Firestore 規則模擬器/手動）**

Run: `grep -nE "match /(comments|ratings)" web/firestore.rules`
Expected: 顯示 `match /comments/{id}` 與 `match /ratings/{uid}` 各一行。

- [ ] **Step 3: Commit**

```bash
git add web/firestore.rules
git commit -m "feat(rules): 每遊戲留言＋評分規則（一人一票、作者/管理員可刪）"
```

---

### Task 2: 前端模組 `web/community.js` ＋ `web/community.css`

**Files:**
- Create: `web/community.js`
- Create: `web/community.css`

**Interfaces:**
- Consumes: `window.__WT = { slug, title }`（由 pwa 注入，Task 3 確保「留言」鈕 `#cm-open` 存在）；`window.__epPause(on,key)`（假暫停 helper）；`./account.js` 匯出 `db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser, isAdmin`。
- Produces: 綁定 `#cm-open` 的留言/評分面板；無對外函式（自啟動模組）。

- [ ] **Step 1: 建立 `web/community.css`**

```css
/* 留言＋評分面板：置中浮層 + 背景遮罩，深色配色與站一致 */
#cm-panel { position: fixed; inset: 0; z-index: 11000; }
#cm-panel[hidden] { display: none; }
#cm-panel .cm-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,.6); }
#cm-panel .cm-dialog {
  position: relative; max-width: 720px; margin: 5vh auto; max-height: 90vh;
  display: flex; flex-direction: column; background: #1b1b1b; color: #eee;
  border-radius: 14px; box-shadow: 0 12px 40px rgba(0,0,0,.6); overflow: hidden;
  font-family: -apple-system, "PingFang TC", "Microsoft JhengHei", sans-serif;
}
#cm-panel .cm-head {
  display: flex; align-items: center; gap: 10px; padding: 12px 16px;
  border-bottom: 1px solid #333;
}
#cm-panel .cm-head .cm-gametitle { font-size: 16px; flex: 0 1 auto; }
#cm-panel .cm-head .cm-auth { margin-left: auto; font-size: 12px; color: #9ca3af; }
#cm-panel .cm-head .cm-close { background: none; border: none; color: #cbd5e1; font-size: 18px; cursor: pointer; }
#cm-panel button { cursor: pointer; }
#cm-panel .cm-auth button, #cm-panel .cm-submit, #cm-panel .cm-del {
  border: 1px solid #3a3a3a; background: #1f2937; color: #cbd5e1;
  border-radius: 8px; padding: 4px 10px; font-size: 13px;
}
#cm-panel .cm-rating { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-bottom: 1px solid #333; }
#cm-panel .cm-avg { color: #fbbf24; font-size: 14px; }
#cm-panel .cm-stars { display: inline-flex; gap: 2px; }
#cm-panel .cm-star { background: none; border: none; font-size: 20px; color: #4b5563; cursor: pointer; padding: 0 2px; }
#cm-panel .cm-star.on { color: #fbbf24; }
#cm-panel .cm-star:disabled { cursor: default; }
#cm-panel .cm-list { overflow: auto; padding: 12px 16px; flex: 1 1 auto; }
#cm-panel .cm-empty { color: #888; }
#cm-panel .cm-item { border: 1px solid #2a2a2a; border-radius: 10px; margin-bottom: 10px; padding: 8px 12px; }
#cm-panel .cm-meta { color: #9ca3af; font-size: 12px; }
#cm-panel .cm-text-body { margin-top: 6px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
#cm-panel .cm-del { margin-top: 8px; border-color: #7f1d1d; color: #fca5a5; }
#cm-panel .cm-compose { border-top: 1px solid #333; padding: 12px 16px; display: flex; gap: 8px; }
#cm-panel .cm-text {
  flex: 1 1 auto; box-sizing: border-box; min-height: 48px; padding: 8px 10px;
  border-radius: 8px; border: 1px solid #333; background: #111; color: #eee; font-size: 14px; resize: vertical;
}
```

- [ ] **Step 2: 建立 `web/community.js`（完整內容）**

```javascript
// 留言＋五星評分面板。依賴頁面注入的 window.__WT（slug/title）與地基 account.js。
import {
  collection, addDoc, getDocs, deleteDoc, doc, setDoc, query, orderBy, serverTimestamp,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser, isAdmin,
} from './account.js';

const GM = window.__WT || { slug: '', title: '' };
let myStars = 0; // 目前使用者的評分（0＝未評）

// ---- 浮層 DOM ----
const panel = document.createElement('div');
panel.id = 'cm-panel';
panel.hidden = true;
panel.innerHTML = `
  <div class="cm-backdrop"></div>
  <div class="cm-dialog">
    <div class="cm-head">
      <strong class="cm-gametitle"></strong>
      <span class="cm-auth"></span>
      <button class="cm-close" type="button">✕</button>
    </div>
    <div class="cm-rating">
      <span class="cm-avg"></span>
      <span class="cm-stars" role="group" aria-label="你的評分"></span>
    </div>
    <div class="cm-list"></div>
    <div class="cm-compose">
      <textarea class="cm-text" maxlength="500" placeholder="留個言…（最多 500 字）"></textarea>
      <button class="cm-submit" type="button">送出</button>
    </div>
  </div>`;
document.body.appendChild(panel);
panel.querySelector('.cm-gametitle').textContent = GM.title || '留言';

const listEl = panel.querySelector('.cm-list');
const authEl = panel.querySelector('.cm-auth');
const avgEl = panel.querySelector('.cm-avg');
const starsEl = panel.querySelector('.cm-stars');
const textEl = panel.querySelector('.cm-text');

function openPanel() {
  panel.hidden = false;
  if (window.__epPause) window.__epPause(true, 'cm');
  loadRatings();
  loadList();
}
function closePanel() {
  panel.hidden = true;
  if (window.__epPause) window.__epPause(false, 'cm');
}

const openBtn = document.getElementById('cm-open');
if (openBtn) openBtn.onclick = () => {
  if (!isReady()) { alert('站長尚未設定後端，留言功能暫不可用'); return; }
  openPanel();
};
panel.querySelector('.cm-close').onclick = closePanel;
panel.querySelector('.cm-backdrop').onclick = closePanel;

// ---- 登入狀態 ----
onAuthChange(renderAuth);
function renderAuth(u) {
  authEl.innerHTML = '';
  if (u) {
    authEl.append(document.createTextNode((u.displayName || '已登入') + ' '));
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = '登出';
    b.onclick = () => signOutUser();
    authEl.append(b);
  } else {
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = '用 Google 登入';
    b.onclick = () => signInWithGoogle().catch(() => alert('登入失敗'));
    authEl.append(b);
  }
  renderStars(); // 登入狀態變了，星星可點性也變
}

// ---- 評分 ----
async function loadRatings() {
  avgEl.textContent = '評分載入中…';
  try {
    const snap = await getDocs(collection(db, 'games', GM.slug, 'ratings'));
    let sum = 0; let n = 0; myStars = 0;
    const u = currentUser();
    snap.forEach((d) => {
      const s = d.data().stars;
      if (typeof s === 'number') { sum += s; n += 1; }
      if (u && d.id === u.uid) myStars = s || 0;
    });
    avgEl.textContent = n ? ('★ ' + (sum / n).toFixed(1) + ' · ' + n + ' 人') : '尚無評分';
    renderStars();
  } catch (e) {
    avgEl.textContent = '評分載入失敗';
  }
}
function renderStars() {
  starsEl.innerHTML = '';
  const u = currentUser();
  for (let k = 1; k <= 5; k += 1) {
    const star = document.createElement('button');
    star.type = 'button';
    star.className = 'cm-star' + (k <= myStars ? ' on' : '');
    star.textContent = '★';
    star.disabled = !u;
    star.title = u ? (k + ' 星') : '登入後可評分';
    star.onclick = () => rate(k);
    starsEl.appendChild(star);
  }
}
async function rate(k) {
  const u = currentUser();
  if (!u) { signInWithGoogle().catch(() => alert('登入失敗')); return; }
  try {
    if (k === myStars) { // 再點同一顆已選的星 → 收回評分
      await deleteDoc(doc(db, 'games', GM.slug, 'ratings', u.uid));
    } else {
      await setDoc(doc(db, 'games', GM.slug, 'ratings', u.uid), {
        stars: k, authorUid: u.uid, updatedAt: serverTimestamp(),
      });
    }
    loadRatings();
  } catch (e) { alert('評分失敗，請稍後再試'); }
}

// ---- 留言清單（一次性查詢）----
async function loadList() {
  listEl.textContent = '載入中…';
  try {
    const q = query(
      collection(db, 'games', GM.slug, 'comments'),
      orderBy('createdAt', 'desc'),
    );
    const snap = await getDocs(q);
    listEl.innerHTML = '';
    if (snap.empty) {
      listEl.innerHTML = '<p class="cm-empty">還沒有留言，搶頭香！</p>';
      return;
    }
    snap.forEach((d) => listEl.appendChild(renderItem(d.id, d.data())));
  } catch (e) {
    listEl.textContent = '載入失敗，請稍後再試';
  }
}
function renderItem(id, data) {
  const item = document.createElement('div');
  item.className = 'cm-item';
  const meta = document.createElement('div');
  meta.className = 'cm-meta';
  const date = (data.createdAt && data.createdAt.toDate)
    ? data.createdAt.toDate().toLocaleString() : '';
  meta.textContent = (data.authorName || '匿名') + ' · ' + date;
  item.appendChild(meta);
  const body = document.createElement('div');
  body.className = 'cm-text-body';
  body.textContent = data.text || ''; // 純文字，textContent → 無 XSS
  item.appendChild(body);

  const u = currentUser();
  if (u && (u.uid === data.authorUid || isAdmin(u.uid))) {
    const del = document.createElement('button');
    del.type = 'button'; del.className = 'cm-del'; del.textContent = '刪除';
    del.onclick = async () => {
      if (!confirm('確定刪除這則留言？')) return;
      try {
        await deleteDoc(doc(db, 'games', GM.slug, 'comments', id));
        loadList();
      } catch (e) { alert('刪除失敗'); }
    };
    item.appendChild(del);
  }
  return item;
}

// ---- 送出留言 ----
panel.querySelector('.cm-submit').onclick = async () => {
  const u = currentUser();
  if (!u) { signInWithGoogle().catch(() => alert('登入失敗')); return; }
  const text = textEl.value.trim();
  if (!text) { alert('請輸入留言'); return; }
  if (text.length > 500) { alert('留言過長（上限 500 字）'); return; }
  try {
    await addDoc(collection(db, 'games', GM.slug, 'comments'), {
      text,
      authorName: u.displayName || '匿名',
      authorUid: u.uid,
      createdAt: serverTimestamp(),
    });
    textEl.value = '';
    loadList();
  } catch (e) { alert('送出失敗，請稍後再試'); }
};
```

- [ ] **Step 3: 語法檢查**

Run: `cp web/community.js _check.mjs && node --check _check.mjs && rm _check.mjs`
Expected: 無輸出（語法正確）。

- [ ] **Step 4: Commit**

```bash
git add web/community.js web/community.css
git commit -m "feat(web): 留言＋五星評分面板（community.js/css）"
```

---

### Task 3: `pwa.py` 注入「留言」鈕＋資產，並補 Python 測試

**Files:**
- Modify: `pwa.py`（`_SAVE_UI` 的 `#saveui` 按鈕列；新增 `_CM_SNIPPET`；`write_game_pages` 的 `body_add`）
- Test: `tests/test_pwa_gamepages.py`、`tests/test_pwa_webassets.py`

**Interfaces:**
- Consumes: `web/community.js`/`web/community.css`（Task 2）— `install_web_assets` 自動複製所有 `web/*.js`/`*.css`，故檔案存在即被複製。
- Produces: 每遊戲頁 `#saveui` 內 `<button id="cm-open">留言</button>` 與 `community.css`/`community.js` 引用。

- [ ] **Step 1: 寫失敗測試（注入）**

在 `tests/test_pwa_gamepages.py` 末尾加：

```python
def test_write_game_pages_injects_community(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    pwa.write_game_pages(dist, [{"label": "甲遊戲", "slug": "g1", "cover_rel": None}])
    html = (dist / "play-g1.html").read_text(encoding="utf-8")
    # 左上角「留言」鈕（和攻略/存檔鈕同個 #saveui 容器）
    assert 'id="cm-open"' in html and "留言" in html
    # 樣式與模組腳本
    assert 'href="community.css"' in html
    assert 'type="module" src="community.js"' in html
```

- [ ] **Step 2: 寫失敗測試（資產複製）**

在 `tests/test_pwa_webassets.py` 的 `test_install_web_assets_copies_js_css` 內，把現有迴圈的名稱元組擴充，加入 community 兩個檔。將：

```python
    for name in ("account.js", "walkthrough.js", "walkthrough.css"):
        assert (dist / name).exists(), name
        assert name in copied
```

改成：

```python
    for name in ("account.js", "walkthrough.js", "walkthrough.css",
                 "community.js", "community.css"):
        assert (dist / name).exists(), name
        assert name in copied
```

- [ ] **Step 3: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_gamepages.py::test_write_game_pages_injects_community tests/test_pwa_webassets.py -v`
Expected: 兩者 FAIL（尚未注入 `cm-open`/`community.*`；且 community.* 尚未在 web/ 被複製——注意：Task 2 已建立 web/community.*，故資產測試只缺「斷言」，注入測試缺 pwa 修改）。

- [ ] **Step 4: 在 `_SAVE_UI` 按鈕列加「留言」鈕**

在 `pwa.py` 找到（約第 191 行）：

```html
<div id="saveui"><button id="wt-open">攻略</button><button id="saveexp">導出存檔</button><button id="saveimp">導入存檔</button>
```

改成（在「攻略」之後加「留言」）：

```html
<div id="saveui"><button id="wt-open">攻略</button><button id="cm-open">留言</button><button id="saveexp">導出存檔</button><button id="saveimp">導入存檔</button>
```

- [ ] **Step 5: 新增 `_CM_SNIPPET` 並接到 `body_add`**

在 `pwa.py` 的 `_WT_SNIPPET = """..."""`（約第 272–279 行）定義之後，新增：

```python
# 留言＋評分：純前端模組（讀 _WT_SNIPPET 注入的 window.__WT；純文字，不需 Quill/DOMPurify）。
_CM_SNIPPET = """
<link rel="stylesheet" href="community.css">
<script type="module" src="community.js"></script>
"""
```

接著在 `write_game_pages` 內找到（約第 391 行）：

```python
        body_add = dl_snippet + save_snippet + wt_snippet
```

改成（在攻略片段之後接上留言片段；`_CM_SNIPPET` 無 `__SLUG__`/`__TITLE__` 佔位符，直接接）：

```python
        body_add = dl_snippet + save_snippet + wt_snippet + _CM_SNIPPET
```

- [ ] **Step 6: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_gamepages.py tests/test_pwa_webassets.py -v`
Expected: PASS（含新注入測試、資產測試與既有測試）。

- [ ] **Step 7: 全測試**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS。

- [ ] **Step 8: Commit**

```bash
git add pwa.py tests/test_pwa_gamepages.py tests/test_pwa_webassets.py
git commit -m "feat(pwa): 注入留言鈕＋community 資產（留言/評分上線）"
```

---

## 收尾：手動驗證（非自動測試）

- [ ] 重建並部署，且 Firestore 規則**重新發布**（本輪規則為擴充，須一併發布）。
- [ ] **評分**：登入→點星評分→平均分與「你的評分」更新；改分→平均更新；再點同星→收回（平均/人數變）；未登入星星不可點。
- [ ] **留言**：登入→送出純文字留言→列表即時更新、另裝置/無痕看得到；作者/管理員有「刪除」、未登入只能看；超長/空白被擋。
- [ ] **暫停整合**：開「留言」面板→音樂停、角色不動、畫面不黑；關閉→恢復。
- [ ] **未設定後端**：firebase-config 仍佔位→點「留言」顯示「站長尚未設定後端」。

## Self-Review 註記（已檢查）

- **Spec 覆蓋**：五星評分(Task2 loadRatings/rate)、平鋪純文字留言(Task2 loadList/submit)、留言鈕入口+評分置頂(Task2 DOM + Task3 注入)、規則(Task1)、注入+資產(Task3)、假暫停整合(Task2 openPanel/closePanel 用 key 'cm')、textContent 防 XSS、長度/權限——皆有對應任務。
- **型別一致**：`window.__WT`(slug/title) 與既有注入一致；account.js 匯出 `db,isReady,currentUser,onAuthChange,signInWithGoogle,signOutUser,isAdmin` 與 walkthrough.js 用法一致；新增 `setDoc` import；評分欄位 `{stars,authorUid,updatedAt}`、留言欄位 `{text,authorName,authorUid,createdAt}` 與規則 hasOnly 白名單一致；doc id＝uid 與規則 `match /ratings/{uid}`、`uid==request.auth.uid` 一致。
- **非自動測試**：Firestore 規則與面板互動屬瀏覽器端，靠收尾手動驗；Python 測涵蓋注入與資產複製；JS 靠 node --check。
