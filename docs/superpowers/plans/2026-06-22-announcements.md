# 公告 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 管理員在首頁內嵌富文字編輯一則站務公告，所有訪客在首頁頂部看到可關閉橫幅，並顯示發布／編輯日期。

**Architecture:** 純前端模組 `web/announce.js`＋`announce.css`（沿用地基 `account.js`），由 `pwa.install_web_assets` 自動複製進 dist。資料存 Firestore 單一固定文件 `announcements/current`。橫幅注入首頁（menu.py），渲染用 DOMPurify；管理員按「編輯」才 lazy-load Quill。

**Tech Stack:** Firebase Firestore（9.23.0 ESM）、Google 登入、Quill 1.3.7、DOMPurify 3.0.8、Python build（menu.py / pwa.py）、pytest、`node --check` 語法驗證。

## Global Constraints

- 設計依據：`docs/superpowers/specs/2026-06-22-announcements-design.md`。
- 資料模型 `announcements/current`：`{ html, createdAt, updatedAt }`；`createdAt` 只首發寫一次。
- 富文字 HTML 上限 50000 bytes；公開內容渲染必經 `DOMPurify.sanitize(html, { ALLOWED_URI_REGEXP: /^(?:https?|mailto):/i })`。
- Firestore 規則沿用既有 `'YOUR_ADMIN_UID'` 佔位符慣例（站長部署時自行替換）。
- 管理員身分＝`account.js` 的 `isAdmin(uid)`；`isReady()` 為 false 時整個橫幅靜默不顯示。
- `web/announce.js`、`announce.css` 受版控、會被自動複製；`web/firebase-config.js`（真實金鑰）維持 gitignored，勿動。
- 關閉鍵：`localStorage['ann-dismissed'] = String(updatedAt.toMillis())`；公告一更新（毫秒改變）就重新跳出；管理員不受 dismissed 影響（永遠看得到以便編輯）。
- CDN 版本對齊攻略頁：`https://cdn.quilljs.com/1.3.7/quill.min.js`、`quill.snow.css`、`https://cdn.jsdelivr.net/npm/dompurify@3.0.8/dist/purify.min.js`。

## File Structure

- Create: `web/announce.js` — 橫幅讀取/渲染/關閉 ＋ 管理員 lazy-load Quill 編輯。
- Create: `web/announce.css` — 橫幅與編輯器樣式。
- Modify: `web/firestore.rules` — 新增 `announcements/current` 規則。
- Modify: `menu.py`（`_PAGE` 模板）— 注入 announce.css / DOMPurify CDN / `#announce` 容器 / announce.js。
- Modify: `tests/test_menu.py` — 注入測試。
- Modify: `tests/test_pwa_webassets.py` — 斷言 announce.js/css 被複製。

---

### Task 1: Firestore 規則加公告（管理員可寫、公開可讀）

**Files:**
- Modify: `web/firestore.rules`

無自動化測試（規則檔是貼進 Firebase Console 的 artifact，repo 內無 emulator 測試框架）——靠手動驗證。本任務只新增一段 match 區塊。

- [ ] **Step 1: 新增公告規則區塊**

在 `web/firestore.rules` 的 `match /databases/{database}/documents {` 內、最後一個 `match /users/{uid}/saves/{slug}` 區塊之後（仍在 documents 區塊的閉合 `}` 之前），加入：

```
      // 公告：公開可讀；只有管理員能寫（單一固定 doc，原地編輯）。
      // merge 寫入後 request.resource.data 為合併後完整狀態，含既有 createdAt，
      // 故 hasOnly(['html','createdAt','updatedAt']) 對「只送 html＋updatedAt 的編輯」仍成立。
      match /announcements/current {
        allow read: if true;
        allow write: if request.auth != null
          && request.auth.uid == 'YOUR_ADMIN_UID'
          && request.resource.data.keys().hasOnly(['html','createdAt','updatedAt'])
          && request.resource.data.html is string
          && request.resource.data.html.size() <= 50000;
      }
```

- [ ] **Step 2: 確認大括號平衡**

Run: `python -c "s=open('web/firestore.rules',encoding='utf-8').read(); assert s.count('{')==s.count('}'), (s.count('{'),s.count('}')); print('braces ok')"`
Expected: 輸出 `braces ok`。

- [ ] **Step 3: Commit**

```bash
git add web/firestore.rules
git commit -m "feat(rules): 公告規則（announcements/current，管理員可寫、公開可讀）"
```

---

### Task 2: menu.py 注入橫幅資產（TDD）

**Files:**
- Modify: `menu.py`（`_PAGE` 模板）
- Test: `tests/test_menu.py`

**Interfaces:**
- Consumes: 既有 `menu.write_menu(dist, app_label, entries, ...) -> Path`（不改簽名）。
- Produces: 首頁 HTML 含 `announce.css`、`announce.js`、DOMPurify CDN、`<div id="announce" hidden>`（位置在 `<div class="toolbar">` 之前）。

- [ ] **Step 1: 寫失敗測試**

在 `tests/test_menu.py` 末尾加：

```python
def test_write_menu_injects_announcements(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    html = menu.write_menu(
        dist, "庫", [{"label": "甲", "slug": "g", "cover_rel": None}]
    ).read_text(encoding="utf-8")
    assert 'href="announce.css"' in html
    assert 'type="module" src="announce.js"' in html
    assert "purify.min.js" in html
    assert 'id="announce"' in html
    # 橫幅容器在工具列之前（DOM 順序）
    assert html.index('id="announce"') < html.index('class="toolbar"')
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_menu.py::test_write_menu_injects_announcements -q`
Expected: FAIL（尚無 announce 資產）。

- [ ] **Step 3: head 加 announce.css ＋ DOMPurify CDN**

在 `menu.py` 找到（約第 79 行）：

```html
<link rel="stylesheet" href="popular.css">
</head>
```

改成：

```html
<link rel="stylesheet" href="popular.css">
<link rel="stylesheet" href="announce.css">
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.8/dist/purify.min.js"></script>
</head>
```

（DOMPurify 為同步 head script，先於 deferred 的 announce.js module 執行，渲染時已就緒。）

- [ ] **Step 4: body 頂加橫幅容器**

在 `menu.py` 找到（約第 82–84 行）：

```html
<header>__TITLE__</header>
<a href="profile.html" id="me-link">👤 我的</a>
<div class="toolbar">
```

改成（在 toolbar 之前插入容器）：

```html
<header>__TITLE__</header>
<a href="profile.html" id="me-link">👤 我的</a>
<div id="announce" hidden></div>
<div class="toolbar">
```

- [ ] **Step 5: body 尾加 announce.js module**

在 `menu.py` 找到（約第 147 行）：

```html
<script type="module" src="popular.js"></script>
</body>
```

改成：

```html
<script type="module" src="popular.js"></script>
<script type="module" src="announce.js"></script>
</body>
```

- [ ] **Step 6: 跑測試**

Run: `python -m pytest tests/test_menu.py -q`
Expected: PASS（含新測試與既有 menu 測試）。

- [ ] **Step 7: Commit**

```bash
git add menu.py tests/test_menu.py
git commit -m "feat(menu): 首頁注入公告橫幅資產（announce.css/js＋DOMPurify＋#announce 容器）"
```

---

### Task 3: 公告前端模組 announce.js＋announce.css

**Files:**
- Create: `web/announce.js`
- Create: `web/announce.css`
- Test: `tests/test_pwa_webassets.py`（擴充既有測試，斷言被自動複製）

**Interfaces:**
- Consumes: `account.js` 的 `db`、`isReady`、`currentUser`、`onAuthChange`、`isAdmin`；全域 `DOMPurify`（menu.py 已注入）、`Quill`（lazy-load）。
- Consumes: 首頁 `#announce` 容器（Task 2 注入）。
- Produces: 無對外 JS API；行為＝橫幅顯示/關閉/管理員編輯。

announce.js 的 Firestore 互動沿用既有「不測前端 SDK 互動」慣例（留言/評分/收藏皆未測）；本任務測試只覆蓋「檔案被 install_web_assets 複製」＋ `node --check` 語法。

- [ ] **Step 1: 擴充 webassets 測試（先失敗）**

在 `tests/test_pwa_webassets.py` 的檔名 tuple（`for name in (...)`）內，於 `"popular.js", "popular.css"` 之後加 `"announce.js", "announce.css",`，使其變為：

```python
                 "popular.js", "popular.css",
                 "announce.js", "announce.css"):
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_webassets.py -q`
Expected: FAIL（`web/announce.js` 尚不存在 → 未被複製）。

- [ ] **Step 3: 建立 `web/announce.css`**

```css
#announce { padding: 0 12px; }
.ann-banner { position: relative; max-width: 900px; margin: 10px auto 0;
  background: #1e293b; border: 1px solid #334155; border-radius: 10px;
  padding: 12px 44px 12px 14px; color: #e2e8f0; }
.ann-tools { position: absolute; top: 6px; right: 8px; display: flex; gap: 4px; }
.ann-tools button { background: transparent; border: 0; color: #94a3b8;
  font-size: 13px; cursor: pointer; padding: 2px 6px; border-radius: 6px; }
.ann-tools button:hover { background: #334155; color: #e2e8f0; }
.ann-body { font-size: 14px; line-height: 1.6; word-break: break-word; }
.ann-body a { color: #93c5fd; }
.ann-body img { max-width: 100%; height: auto; }
.ann-empty { color: #94a3b8; }
.ann-meta { margin-top: 6px; font-size: 12px; color: #94a3b8; }
.ann-editor { margin-top: 8px; }
.ann-quill { background: #fff; color: #111; border-radius: 6px; min-height: 120px; }
.ann-editbar { margin-top: 8px; display: flex; gap: 8px; }
.ann-editbar button { padding: 4px 14px; border-radius: 6px; border: 0;
  background: #2563eb; color: #fff; cursor: pointer; font-size: 13px; }
.ann-editbar button.ann-cancel { background: #334155; }
```

- [ ] **Step 4: 建立 `web/announce.js`**

```javascript
// 站務公告：首頁頂部橫幅（單則，可關閉）；管理員可內嵌富文字編輯。依賴地基 account.js。
import {
  doc, getDoc, setDoc, serverTimestamp,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, isAdmin,
} from './account.js';

const host = document.getElementById('announce');
if (host && isReady()) init();

function init() {
  let data = null;        // { html, createdAt, updatedAt } 或 null
  let isAdminNow = false;
  let quill = null;
  let quillLoading = null;

  // ---- 橫幅 DOM ----
  const banner = document.createElement('div');
  banner.className = 'ann-banner';
  const tools = document.createElement('div');
  tools.className = 'ann-tools';
  const editBtn = document.createElement('button');
  editBtn.type = 'button'; editBtn.className = 'ann-edit'; editBtn.textContent = '✎ 編輯'; editBtn.hidden = true;
  const closeBtn = document.createElement('button');
  closeBtn.type = 'button'; closeBtn.className = 'ann-close'; closeBtn.textContent = '✕'; closeBtn.title = '關閉';
  tools.append(editBtn, closeBtn);
  const body = document.createElement('div');
  body.className = 'ann-body';
  const meta = document.createElement('div');
  meta.className = 'ann-meta';
  const editor = document.createElement('div');
  editor.className = 'ann-editor'; editor.hidden = true;
  const quillEl = document.createElement('div');
  quillEl.className = 'ann-quill';
  const editbar = document.createElement('div');
  editbar.className = 'ann-editbar';
  const submit = document.createElement('button');
  submit.type = 'button'; submit.textContent = '送出';
  const cancel = document.createElement('button');
  cancel.type = 'button'; cancel.className = 'ann-cancel'; cancel.textContent = '取消';
  editbar.append(submit, cancel);
  editor.append(quillEl, editbar);
  banner.append(tools, body, meta, editor);
  host.appendChild(banner);

  function dateStr(ts) {
    return (ts && ts.toDate) ? ts.toDate().toLocaleDateString() : '';
  }
  function version() {
    return (data && data.updatedAt && data.updatedAt.toMillis) ? String(data.updatedAt.toMillis()) : '';
  }

  // ---- 渲染（顯示邏輯的單一來源）----
  function render() {
    if (!editor.hidden) return;   // 編輯中不重繪
    editBtn.hidden = !isAdminNow;
    const html = data && data.html ? data.html : '';

    if (!html) {                  // 無公告
      if (isAdminNow) {           // 管理員：顯示空橫幅以便首發
        body.innerHTML = '<em class="ann-empty">（目前沒有公告，按「編輯」發布）</em>';
        meta.textContent = '';
        closeBtn.hidden = true;
        host.hidden = false;
      } else {
        host.hidden = true;
      }
      return;
    }

    // 有公告：一般訪客若已關閉同版則隱藏；管理員永遠看得到
    let dismissed = '';
    try { dismissed = localStorage.getItem('ann-dismissed') || ''; } catch (e) { /* 無 storage */ }
    if (!isAdminNow && version() && dismissed === version()) { host.hidden = true; return; }

    body.innerHTML = DOMPurify.sanitize(html, { ALLOWED_URI_REGEXP: /^(?:https?|mailto):/i });
    const c = dateStr(data.createdAt);
    const u = dateStr(data.updatedAt);
    meta.textContent = c ? ('發布於 ' + c + (u && u !== c ? ' · 編輯於 ' + u : '')) : '';
    closeBtn.hidden = false;
    host.hidden = false;
  }

  closeBtn.onclick = () => {
    if (version()) {
      try { localStorage.setItem('ann-dismissed', version()); } catch (e) { /* 無 storage */ }
    }
    host.hidden = true;
  };

  // ---- 讀取 ----
  async function load() {
    try {
      const snap = await getDoc(doc(db, 'announcements', 'current'));
      data = snap.exists() ? snap.data() : null;
    } catch (e) { data = null; }
    render();
  }

  // ---- 管理員身分 ----
  onAuthChange((user) => {
    isAdminNow = !!(user && isAdmin(user.uid));
    render();
  });

  // ---- 編輯（lazy-load Quill）----
  function ensureQuill() {
    if (window.Quill) return Promise.resolve();
    if (quillLoading) return quillLoading;
    quillLoading = new Promise((resolve, reject) => {
      const css = document.createElement('link');
      css.rel = 'stylesheet'; css.href = 'https://cdn.quilljs.com/1.3.7/quill.snow.css';
      document.head.appendChild(css);
      const s = document.createElement('script');
      s.src = 'https://cdn.quilljs.com/1.3.7/quill.min.js';
      s.onload = resolve;
      s.onerror = () => reject(new Error('Quill 載入失敗'));
      document.head.appendChild(s);
    });
    return quillLoading;
  }

  editBtn.onclick = async () => {
    try { await ensureQuill(); } catch (e) { alert('編輯器載入失敗，請稍後再試'); return; }
    if (!quill) {
      quill = new Quill(quillEl, {
        theme: 'snow',
        modules: {
          toolbar: [
            [{ header: [1, 2, 3, false] }],
            ['bold', 'italic'],
            [{ list: 'ordered' }, { list: 'bullet' }],
            ['link'],
          ],
        },
      });
    }
    quill.clipboard.dangerouslyPasteHTML((data && data.html) || '');
    body.hidden = true; meta.hidden = true; tools.hidden = true;
    editor.hidden = false;
    host.hidden = false;
  };

  function closeEditor() {
    editor.hidden = true;
    body.hidden = false; meta.hidden = false; tools.hidden = false;
    render();
  }
  cancel.onclick = closeEditor;

  submit.onclick = async () => {
    const u = currentUser();
    if (!u || !isAdmin(u.uid)) { alert('沒有權限'); return; }
    const text = quill.getText().trim();
    const html = text ? quill.root.innerHTML : '';   // 全空 → 存空字串（對所有人隱藏公告）
    if (new Blob([html]).size > 50000) { alert('內文過長，請精簡'); return; }
    const payload = { html, updatedAt: serverTimestamp() };
    if (!(data && data.createdAt)) payload.createdAt = serverTimestamp();  // 首發才寫 createdAt
    try {
      await setDoc(doc(db, 'announcements', 'current'), payload, { merge: true });
    } catch (e) { alert('儲存失敗，請稍後再試'); return; }
    try { localStorage.removeItem('ann-dismissed'); } catch (e) { /* 無 storage */ }
    editor.hidden = true;
    body.hidden = false; meta.hidden = false; tools.hidden = false;
    await load();
  };

  load();
}
```

- [ ] **Step 5: 驗證 announce.js 語法**

Run: `node --check web/announce.js`
Expected: 無輸出（ES module 語法正確；`node --check` 不解析 import 來源，只驗語法）。

- [ ] **Step 6: 跑 webassets 測試**

Run: `python -m pytest tests/test_pwa_webassets.py -q`
Expected: PASS（announce.js/css 已被 install_web_assets 複製）。

- [ ] **Step 7: 全測試**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS。

- [ ] **Step 8: Commit**

```bash
git add web/announce.js web/announce.css tests/test_pwa_webassets.py
git commit -m "feat(web): 公告模組 announce.js/css（橫幅＋管理員 Quill 編輯）"
```

---

## 收尾：手動驗證

- [ ] 重建並部署；Firestore Console 把規則的 `'YOUR_ADMIN_UID'` 替換成真實 admin uid 後發佈。
- [ ] 管理員登入首頁 → 出現「✎ 編輯」→ 寫富文字 → 橫幅顯示「發布於 今天」。
- [ ] 再次編輯 → 橫幅顯示「發布於 … · 編輯於 …」。
- [ ] 一般訪客（無痕）→ 看到橫幅 → 關閉 → 重整不再出現；管理員再編輯 → 重新跳出。
- [ ] 公告清空送出 → 所有人都不再看到橫幅；管理員仍看到空橫幅可再發。
- [ ] 站長未設後端（`isReady()` false）→ 首頁無橫幅、無 console 錯誤。

## Self-Review 註記（已檢查）
- **Spec 覆蓋**：資料模型（createdAt/updatedAt）→ Task 1 規則＋Task 3 submit 寫入；橫幅顯示/日期/關閉/dismiss → Task 3 render；管理員 lazy-load Quill 編輯 → Task 3 editBtn；menu.py 注入＋DOMPurify → Task 2；資產自動複製 → Task 3 webassets 測試。
- **無佔位符**：所有程式碼、檔案路徑、指令、預期輸出皆完整。
- **型別/命名一致**：`announcements/current`、`ann-dismissed`、`isAdminNow`、`version()`、`render()` 全程一致；CDN 版本對齊攻略頁。
- **刻意省略**（YAGNI）：公告歷史/多則、作者顯示、Markdown、圖片上傳 handler——不在本計畫。
