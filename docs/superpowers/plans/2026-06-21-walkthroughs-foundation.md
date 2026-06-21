# 社群地基＋攻略投稿 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在每個遊戲頁左上角加「攻略」鈕，開面板可讀/投稿該遊戲攻略；後端用 Firebase（Firestore＋Google 登入），地基設計成可重用。

**Architecture:** 新增 `web/` 下的前端 ES 模組（`account.js` 地基、`walkthrough.js` 功能、`walkthrough.css`、`firebase-config.js` 設定、`firestore.rules` 規則）；建置時 `pwa.install_web_assets` 把 js/css 複製進 `dist/`，`pwa.write_game_pages` 在每頁注入「攻略」鈕＋設定＋CDN/模組 script。攻略存 Firestore `games/<slug>/walkthroughs`，圖片自動上傳免費圖床只存網址，顯示時 DOMPurify 消毒。

**Tech Stack:** Firebase JS SDK 9.23.0（gstatic 模組）、Quill 1.3.7（全域）、DOMPurify 3.0.8（全域）、imgur 匿名上傳 API；Python（pwa/build 整合）、pytest、node（JS 語法檢查）。

## Global Constraints

- Firestore 路徑：`games/<slug>/walkthroughs/<自動id>`；每筆欄位 `{ title, html, authorName, authorUid, createdAt }`。
- 長度限制：標題 1–200 字元、內文 HTML ≤50,000 字元；圖片檔 ≤5 MB。
- 投稿＝Google 登入即可、立即公開；刪除＝作者本人或管理員（`ADMIN_UID`）；不允許 update。
- 圖片：**不可 base64 內嵌**；自動上傳到圖床（預設 imgur，Client-ID 設定），HTML 只存圖片網址。
- 顯示任何使用者 HTML 一律 `DOMPurify.sanitize` 後才插入 DOM。
- 攻略清單用一次性 `getDocs` 查詢（非即時監聽），投稿/刪除後重查。
- Firebase web config 非機密；`firebase-config.js`/`firestore.rules` 內的 `YOUR_*`/`ADMIN_UID` 由站長填。
- Firebase SDK 版本固定 `9.23.0`、Quill `1.3.7`。
- 既有測試指令：`python -m pytest <path> -v`（repo 根目錄）。JS 語法檢查：`cp web/X.js _check.mjs && node --check _check.mjs && rm _check.mjs`。

---

### Task 1: Firebase 設定範本 ＋ Firestore 規則

**Files:**
- Create: `web/firebase-config.js`
- Create: `web/firestore.rules`

**Interfaces:**
- Produces: `firebase-config.js` 匯出 `firebaseConfig`（物件）、`ADMIN_UID`（字串）、`imageUpload`（`{provider, clientId}`）。

- [ ] **Step 1: 建立 `web/firebase-config.js`**

```javascript
// 站長填入：Firebase 專案 web config（Firebase Console → 專案設定 → 您的應用程式 → 網頁應用程式）。
// 這些值非機密（安全靠 Firestore 規則）。填好後重新「重建並部署」即生效。
export const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT",
  storageBucket: "YOUR_PROJECT.firebasestorage.app",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID",
};

// 站長的 Google uid（自己登入後可在 Firebase Console 的 Authentication 使用者列表查到）。
// 前端據此顯示「刪除任意攻略」；真正把關在 Firestore 規則。
export const ADMIN_UID = "YOUR_ADMIN_UID";

// 圖床設定：imgur 匿名上傳需 Client-ID（到 imgur 申請應用程式即得，免費、免綁卡）。
export const imageUpload = { provider: "imgur", clientId: "YOUR_IMGUR_CLIENT_ID" };
```

- [ ] **Step 2: 建立 `web/firestore.rules`**

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 攻略：公開可讀；登入才能建立（且作者＝本人、標題/內文長度受限）；
    // 刪除＝作者本人或管理員；不允許修改。
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
            || request.auth.uid == 'YOUR_ADMIN_UID');
      allow update: if false;
    }
  }
}
```

- [ ] **Step 3: 檢查 config 語法**

Run: `cp web/firebase-config.js _check.mjs && node --check _check.mjs && rm _check.mjs`
Expected: 無輸出（語法正確）。

- [ ] **Step 4: Commit**

```bash
git add web/firebase-config.js web/firestore.rules
git commit -m "feat(web): Firebase 設定範本與 Firestore 安全規則（攻略地基）"
```

---

### Task 2: account.js（可重用地基模組）

**Files:**
- Create: `web/account.js`

**Interfaces:**
- Consumes: `./firebase-config.js`（`firebaseConfig`, `ADMIN_UID`）。
- Produces（匯出）：`db`、`auth`、`ADMIN_UID`、`isReady()`、`currentUser()`、`onAuthChange(cb)`、`signInWithGoogle()`、`signOutUser()`、`isAdmin(uid)`。

- [ ] **Step 1: 建立 `web/account.js`**

```javascript
// 共用地基：初始化 Firebase、Google 登入、Firestore handle。
// 之後留言/評分/收藏…等功能都 import 這支。
import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-app.js';
import {
  getAuth, GoogleAuthProvider, signInWithPopup,
  signOut as fbSignOut, onAuthStateChanged,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-auth.js';
import { getFirestore } from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import { firebaseConfig, ADMIN_UID } from './firebase-config.js';

let app, auth, db, ok = false;
try {
  app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  db = getFirestore(app);
  ok = true;
} catch (e) {
  console.error('Firebase 初始化失敗', e);
}

export { db, auth, ADMIN_UID };

// 設定檔還是佔位符（YOUR_*）時視為「未設定」，讓 UI 給友善提示而非報錯。
export function isReady() {
  return ok && !String(firebaseConfig.apiKey || '').startsWith('YOUR_');
}
export function currentUser() { return auth ? auth.currentUser : null; }
export function onAuthChange(cb) { if (auth) onAuthStateChanged(auth, cb); }
export function signInWithGoogle() { return signInWithPopup(auth, new GoogleAuthProvider()); }
export function signOutUser() { return fbSignOut(auth); }
export function isAdmin(uid) { return !!uid && uid === ADMIN_UID; }
```

- [ ] **Step 2: 檢查語法**

Run: `cp web/account.js _check.mjs && node --check _check.mjs && rm _check.mjs`
Expected: 無輸出（語法正確）。

- [ ] **Step 3: Commit**

```bash
git add web/account.js
git commit -m "feat(web): account.js 共用地基（Firebase init/Google 登入/db）"
```

---

### Task 3: walkthrough.css（面板樣式）

**Files:**
- Create: `web/walkthrough.css`

- [ ] **Step 1: 建立 `web/walkthrough.css`**

```css
/* 攻略面板：置中浮層 + 背景遮罩，深色配色與站一致 */
#wt-panel { position: fixed; inset: 0; z-index: 11000; }
#wt-panel[hidden] { display: none; }
#wt-panel .wt-backdrop { position: absolute; inset: 0; background: rgba(0,0,0,.6); }
#wt-panel .wt-dialog {
  position: relative; max-width: 720px; margin: 5vh auto; max-height: 90vh;
  display: flex; flex-direction: column; background: #1b1b1b; color: #eee;
  border-radius: 14px; box-shadow: 0 12px 40px rgba(0,0,0,.6); overflow: hidden;
  font-family: -apple-system, "PingFang TC", "Microsoft JhengHei", sans-serif;
}
#wt-panel .wt-head {
  display: flex; align-items: center; gap: 10px; padding: 12px 16px;
  border-bottom: 1px solid #333;
}
#wt-panel .wt-head .wt-gametitle { font-size: 16px; flex: 0 1 auto; }
#wt-panel .wt-head .wt-auth { margin-left: auto; font-size: 12px; color: #9ca3af; }
#wt-panel .wt-head .wt-close { background: none; border: none; color: #cbd5e1; font-size: 18px; cursor: pointer; }
#wt-panel button { cursor: pointer; }
#wt-panel .wt-auth button, #wt-panel .wt-new, #wt-panel .wt-submit, #wt-panel .wt-cancel, #wt-panel .wt-del {
  border: 1px solid #3a3a3a; background: #1f2937; color: #cbd5e1;
  border-radius: 8px; padding: 4px 10px; font-size: 13px;
}
#wt-panel .wt-list { overflow: auto; padding: 12px 16px; flex: 1 1 auto; }
#wt-panel .wt-empty { color: #888; }
#wt-panel .wt-item { border: 1px solid #2a2a2a; border-radius: 10px; margin-bottom: 10px; padding: 8px 12px; }
#wt-panel .wt-item summary { cursor: pointer; color: #e5e7eb; }
#wt-panel .wt-body { margin-top: 8px; line-height: 1.7; word-break: break-word; }
#wt-panel .wt-body img { max-width: 100%; height: auto; border-radius: 6px; }
#wt-panel .wt-del { margin-top: 8px; border-color: #7f1d1d; color: #fca5a5; }
#wt-panel .wt-compose { border-top: 1px solid #333; padding: 12px 16px; }
#wt-panel .wt-title {
  width: 100%; box-sizing: border-box; margin-bottom: 8px; padding: 8px 10px;
  border-radius: 8px; border: 1px solid #333; background: #111; color: #eee; font-size: 15px;
}
#wt-panel .wt-quill { background: #fff; color: #111; border-radius: 8px; min-height: 160px; }
#wt-panel .wt-editor-bar { margin-top: 8px; display: flex; gap: 8px; }
```

- [ ] **Step 2: 確認檔案存在**

Run: `test -f web/walkthrough.css && echo OK`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add web/walkthrough.css
git commit -m "feat(web): walkthrough.css 攻略面板樣式"
```

---

### Task 4: walkthrough.js（攻略面板功能）

**Files:**
- Create: `web/walkthrough.js`

**Interfaces:**
- Consumes: `./account.js`（`db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser, isAdmin`）、`./firebase-config.js`（`imageUpload`）、全域 `Quill`、`DOMPurify`、頁面注入的 `window.__WT = { slug, title }`、頁面上的 `#wt-open` 按鈕。
- Produces: 在頁面建立 `#wt-panel` 浮層並綁定行為（無對外匯出）。

- [ ] **Step 1: 建立 `web/walkthrough.js`**

```javascript
// 攻略面板：讀/投稿/刪除某遊戲的攻略。依賴頁面注入的 window.__WT 與全域 Quill/DOMPurify。
import {
  collection, addDoc, getDocs, deleteDoc, doc, query, orderBy, serverTimestamp,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser, isAdmin,
} from './account.js';
import { imageUpload } from './firebase-config.js';

const WT = window.__WT || { slug: '', title: '' };
let quill = null;

// ---- 浮層 DOM ----
const panel = document.createElement('div');
panel.id = 'wt-panel';
panel.hidden = true;
panel.innerHTML = `
  <div class="wt-backdrop"></div>
  <div class="wt-dialog">
    <div class="wt-head">
      <strong class="wt-gametitle"></strong>
      <span class="wt-auth"></span>
      <button class="wt-close" type="button">✕</button>
    </div>
    <div class="wt-list"></div>
    <div class="wt-compose">
      <button class="wt-new" type="button">＋ 投稿攻略</button>
      <div class="wt-editor" hidden>
        <input class="wt-title" type="text" maxlength="200" placeholder="攻略標題…">
        <div class="wt-quill"></div>
        <div class="wt-editor-bar">
          <button class="wt-submit" type="button">送出</button>
          <button class="wt-cancel" type="button">取消</button>
        </div>
      </div>
    </div>
  </div>`;
document.body.appendChild(panel);
panel.querySelector('.wt-gametitle').textContent = WT.title || '攻略';

const listEl = panel.querySelector('.wt-list');
const authEl = panel.querySelector('.wt-auth');
const editorEl = panel.querySelector('.wt-editor');
const quillEl = panel.querySelector('.wt-quill');
const titleEl = panel.querySelector('.wt-title');

function openPanel() { panel.hidden = false; loadList(); }
function closePanel() { panel.hidden = true; }

const openBtn = document.getElementById('wt-open');
if (openBtn) openBtn.onclick = () => {
  if (!isReady()) { alert('站長尚未設定後端，攻略功能暫不可用'); return; }
  openPanel();
};
panel.querySelector('.wt-close').onclick = closePanel;
panel.querySelector('.wt-backdrop').onclick = closePanel;

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
}

// ---- 攻略清單（一次性查詢）----
async function loadList() {
  listEl.textContent = '載入中…';
  try {
    const q = query(
      collection(db, 'games', WT.slug, 'walkthroughs'),
      orderBy('createdAt', 'desc'),
    );
    const snap = await getDocs(q);
    listEl.innerHTML = '';
    if (snap.empty) {
      listEl.innerHTML = '<p class="wt-empty">還沒有攻略，來當第一個投稿的人！</p>';
      return;
    }
    snap.forEach((d) => listEl.appendChild(renderItem(d.id, d.data())));
  } catch (e) {
    listEl.textContent = '載入失敗，請稍後再試';
  }
}

function renderItem(id, data) {
  const item = document.createElement('details');
  item.className = 'wt-item';
  const sum = document.createElement('summary');
  const date = (data.createdAt && data.createdAt.toDate)
    ? data.createdAt.toDate().toLocaleDateString() : '';
  sum.textContent = (data.title || '(無標題)') + ' — '
    + (data.authorName || '匿名') + ' ' + date;
  item.appendChild(sum);

  const body = document.createElement('div');
  body.className = 'wt-body';
  body.innerHTML = DOMPurify.sanitize(data.html || '');  // 公開內容必經消毒
  item.appendChild(body);

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
}

// ---- 圖片自動上傳（不走 base64）----
async function uploadImage(file) {
  if (imageUpload.provider === 'imgur') {
    const form = new FormData();
    form.append('image', file);
    const res = await fetch('https://api.imgur.com/3/image', {
      method: 'POST',
      headers: { Authorization: 'Client-ID ' + imageUpload.clientId },
      body: form,
    });
    if (!res.ok) throw new Error('imgur ' + res.status);
    const j = await res.json();
    return j.data.link;
  }
  throw new Error('未設定圖床');
}

function imageHandler() {
  const input = document.createElement('input');
  input.type = 'file'; input.accept = 'image/*';
  input.onchange = async () => {
    const file = input.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { alert('圖片過大（上限 5MB）'); return; }
    const range = quill.getSelection(true);
    const ph = '（圖片上傳中…）';
    quill.insertText(range.index, ph);
    try {
      const url = await uploadImage(file);
      quill.deleteText(range.index, ph.length);
      quill.insertEmbed(range.index, 'image', url);
      quill.setSelection(range.index + 1);
    } catch (e) {
      quill.deleteText(range.index, ph.length);
      alert('圖片上傳失敗，可改貼網址或稍後再試');
    }
  };
  input.click();
}

// ---- 投稿編輯器 ----
panel.querySelector('.wt-new').onclick = () => {
  if (!currentUser()) { signInWithGoogle().catch(() => alert('登入失敗')); return; }
  editorEl.hidden = false;
  if (!quill) {
    quill = new Quill(quillEl, {
      theme: 'snow',
      modules: {
        toolbar: {
          container: [
            [{ header: [1, 2, 3, false] }],
            ['bold', 'italic'],
            [{ list: 'ordered' }, { list: 'bullet' }],
            ['link', 'image'],
          ],
          handlers: { image: imageHandler },
        },
      },
    });
  }
};
panel.querySelector('.wt-cancel').onclick = () => { editorEl.hidden = true; };
panel.querySelector('.wt-submit').onclick = async () => {
  const u = currentUser();
  if (!u) { alert('請先登入'); return; }
  const title = titleEl.value.trim();
  const html = quill ? quill.root.innerHTML : '';
  if (!title) { alert('請輸入標題'); return; }
  if (title.length > 200) { alert('標題過長（上限 200 字）'); return; }
  if (html.length > 50000) { alert('內文過長'); return; }
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

- [ ] **Step 2: 檢查語法**

Run: `cp web/walkthrough.js _check.mjs && node --check _check.mjs && rm _check.mjs`
Expected: 無輸出（語法正確）。

- [ ] **Step 3: Commit**

```bash
git add web/walkthrough.js
git commit -m "feat(web): walkthrough.js 攻略面板（讀/投稿/刪除/圖片上傳）"
```

---

### Task 5: pwa.install_web_assets ＋ 建置整合

**Files:**
- Modify: `pwa.py`（新增 `WEB_DIR`、`install_web_assets`）
- Modify: `easyrpg_web_build.py`（`build_library` 內呼叫）
- Test: `tests/test_pwa_webassets.py`

**Interfaces:**
- Consumes: `web/` 下的 `account.js`/`walkthrough.js`/`walkthrough.css`/`firebase-config.js`（Task 1–4 已建立）。
- Produces: `pwa.install_web_assets(dist) -> list`（複製的檔名清單）。

- [ ] **Step 1: 寫失敗測試**

建立 `tests/test_pwa_webassets.py`：

```python
import pwa


def test_install_web_assets_copies_js_css(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    copied = pwa.install_web_assets(dist)
    # 地基與功能的前端資產都複製進 dist
    for name in ("account.js", "walkthrough.js", "walkthrough.css", "firebase-config.js"):
        assert (dist / name).exists(), name
        assert name in copied
    # 規則檔是給 Console 用的 artifact，不部署
    assert not (dist / "firestore.rules").exists()
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_webassets.py -v`
Expected: FAIL（`pwa.install_web_assets` 未定義）。

- [ ] **Step 3: 在 `pwa.py` 新增函式**

在 `pwa.py` 頂端 import 區下方（`ICON_REL = "icons/icon.png"` 附近）加：

```python
WEB_DIR = Path(__file__).resolve().parent / "web"
```

在 `write_service_worker` 之後（或檔案任一處）加：

```python
def install_web_assets(dist) -> list:
    """把 web/ 下的前端資產（js/css）複製進 dist；回傳複製的檔名清單。

    firebase-config.js 含站長填的設定一併複製；firestore.rules 是給 Firestore
    Console 貼的 artifact，不複製進 dist。
    """
    dist = Path(dist)
    copied = []
    if WEB_DIR.exists():
        for p in sorted(WEB_DIR.iterdir()):
            if p.is_file() and p.suffix in (".js", ".css"):
                shutil.copy2(p, dist / p.name)
                copied.append(p.name)
    return copied
```

（`pwa.py` 已 import `shutil` 與 `from pathlib import Path`，不需再加。）

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_webassets.py -v`
Expected: PASS。

- [ ] **Step 5: 在 `build_library` 呼叫**

`easyrpg_web_build.py` 找到產生遊戲頁前的位置（`menu.write_menu(...)` 那行附近，約 178 行），在它**之前**加一行：

```python
    pwa.install_web_assets(out)   # 複製前端資產（account.js/walkthrough.js/…）進 dist
```

- [ ] **Step 6: 跑全測試確認沒壞**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS（含既有測試）。

- [ ] **Step 7: Commit**

```bash
git add pwa.py easyrpg_web_build.py tests/test_pwa_webassets.py
git commit -m "feat(build): install_web_assets 複製前端資產進 dist"
```

---

### Task 6: 遊戲頁注入「攻略」鈕與腳本

**Files:**
- Modify: `pwa.py`（`_SAVE_UI` 加按鈕；`write_game_pages` 注入攻略片段）
- Test: `tests/test_pwa_gamepages.py`

**Interfaces:**
- Consumes: `dist/walkthrough.js`、`dist/walkthrough.css`（Task 5 複製）。
- Produces: 每頁 `play-<slug>.html` 含 `#wt-open` 按鈕、`window.__WT`、Quill/DOMPurify CDN、`walkthrough.css`/`walkthrough.js`。

- [ ] **Step 1: 寫失敗測試**

在 `tests/test_pwa_gamepages.py` 末尾加：

```python
def test_write_game_pages_injects_walkthrough(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    pwa.write_game_pages(dist, [{"label": "甲遊戲", "slug": "g1", "cover_rel": None}])
    html = (dist / "play-g1.html").read_text(encoding="utf-8")
    # 左上角「攻略」鈕（和存檔鈕同個 #saveui 容器，沿用全螢幕隱藏）
    assert 'id="wt-open"' in html and "攻略" in html
    # 該遊戲的設定（slug/title）注入給腳本
    assert 'window.__WT=' in html
    assert '"g1"' in html and '"甲遊戲"' in html
    # Quill / DOMPurify / 模組腳本與樣式
    assert "quill" in html and "purify" in html
    assert 'href="walkthrough.css"' in html
    assert 'type="module" src="walkthrough.js"' in html
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_gamepages.py::test_write_game_pages_injects_walkthrough -v`
Expected: FAIL（尚未注入）。

- [ ] **Step 3: 在 `_SAVE_UI` 的 `#saveui` 加「攻略」鈕**

`pwa.py` 的 `_SAVE_UI` 裡，把：

```html
<div id="saveui"><button id="saveexp">導出存檔</button><button id="saveimp">導入存檔</button>
```

改成（在最前面加攻略鈕，讓它和存檔鈕同排、共用全螢幕隱藏）：

```html
<div id="saveui"><button id="wt-open">攻略</button><button id="saveexp">導出存檔</button><button id="saveimp">導入存檔</button>
```

- [ ] **Step 4: 新增攻略注入片段常數**

在 `pwa.py` 的 `_SAVE_UI = r"""..."""` 之後加一個模板常數：

```python
# 攻略：Quill/DOMPurify（全域）＋ 該遊戲設定 ＋ 樣式/模組腳本。
# __SLUG__/__TITLE__ 會被替換成 JSON 字串字面值。
_WT_SNIPPET = """
<link href="https://cdn.quilljs.com/1.3.7/quill.snow.css" rel="stylesheet">
<link rel="stylesheet" href="walkthrough.css">
<script src="https://cdn.quilljs.com/1.3.7/quill.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.8/dist/purify.min.js"></script>
<script>window.__WT={slug:__SLUG__,title:__TITLE__};</script>
<script type="module" src="walkthrough.js"></script>
"""
```

- [ ] **Step 5: 在 `write_game_pages` 注入攻略片段**

`write_game_pages` 內，找到目前組 `save_snippet` 並注入 body 的這段：

```python
        save_snippet = _SAVE_UI.replace("__SLUG__", slug_js)
        body_add = dl_snippet + save_snippet
        if "</body>" in html:
            html = html.replace("</body>", body_add + "</body>", 1)
        else:
            html = html + body_add
```

改成（加上 `_WT_SNIPPET`，標題用 JSON 字面值並擋 `</script>` 注入）：

```python
        save_snippet = _SAVE_UI.replace("__SLUG__", slug_js)
        wt_title_js = json.dumps(label).replace("<", "\\u003c")
        wt_snippet = (_WT_SNIPPET
                      .replace("__SLUG__", slug_js)
                      .replace("__TITLE__", wt_title_js))
        body_add = dl_snippet + save_snippet + wt_snippet
        if "</body>" in html:
            html = html.replace("</body>", body_add + "</body>", 1)
        else:
            html = html + body_add
```

（`json` 已在 `pwa.py` import；`slug_js = json.dumps(slug)` 已在迴圈上方定義。）

- [ ] **Step 6: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_gamepages.py -v`
Expected: PASS（含新測試與既有存檔 UI 測試）。

- [ ] **Step 7: 跑全測試**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS。

- [ ] **Step 8: Commit**

```bash
git add pwa.py tests/test_pwa_gamepages.py
git commit -m "feat(pwa): 遊戲頁左上角注入「攻略」鈕與面板腳本"
```

---

## 收尾：站長設定與手動驗證（非自動測試）

- [ ] 站長一次性設定：建 Firebase 專案 → 開 Firestore（Production mode）＋ Authentication 啟用 Google → 複製 web config 貼進 `web/firebase-config.js`、填 `ADMIN_UID`（自己的 uid）與 imgur `clientId`；把 `web/firestore.rules`（`YOUR_ADMIN_UID` 換成自己的 uid）貼進 Firestore Console 的 Rules 發布。
- [ ] 「重建並部署到網頁」→ 進任一遊戲頁 → 左上角「攻略」→ Google 登入 → 投稿（含插入圖片，確認圖片自動上傳、攻略 HTML 存的是圖片網址而非 base64）→ 用無痕視窗（未登入）看得到 → 作者/管理員可刪。

## Self-Review 註記（已檢查）

- **Spec 覆蓋**：地基(account.js/firebase-config/rules，Task 1–2)、攻略讀寫刪(walkthrough.js，Task 4)、圖片自動上傳(Task 4)、DOMPurify 消毒(Task 4)、樣式(Task 3)、建置複製資產(Task 5)、遊戲頁注入鈕(Task 6)、管理員刪除(rules＋isAdmin)、未設定友善提示(isReady) 皆有對應任務。
- **型別一致**：Firestore 路徑 `games/<slug>/walkthroughs`、欄位 `{title,html,authorName,authorUid,createdAt}`、長度限制（200/50000/5MB）、SDK 9.23.0、Quill 1.3.7 全程一致；`account.js` 匯出名與 `walkthrough.js` 匯入名相符。
- **非自動測試**：Firebase/Quill/imgur 互動屬瀏覽器端，靠收尾手動驗證；Python 測試涵蓋注入與資產複製。
