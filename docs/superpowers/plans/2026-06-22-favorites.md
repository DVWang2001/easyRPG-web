# 遊戲收藏 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 讓登入使用者收藏遊戲：首頁卡片與遊戲頁各有 ❤，首頁可「只看收藏」；收藏私有存 Firestore。

**Architecture:** 疊在既有地基上。新增 `web/favorites.js`（一支同時處理首頁卡片與遊戲頁單顆 ❤）＋ `web/favorites.css`；`menu.py` 注入首頁 UI、`pwa.py` 注入遊戲頁 ❤；規則擴充 `web/firestore.rules`。資料存 `users/<uid>/favorites/<slug>`（私有）。

**Tech Stack:** Firebase 9.23.0（gstatic CDN 模組）、純前端 ES module、Python build（menu.py/pwa.py）、pytest。

## Global Constraints

- 設計依據：`docs/superpowers/specs/2026-06-22-favorites-design.md`。
- Firebase SDK 固定 `https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js`。
- 收藏私有：`users/<uid>/favorites/<slug>` 只有 `request.auth.uid == uid` 能讀寫；欄位只允許 `addedAt`。
- slug 當 doc id；首頁卡片 slug 從 `href="play-<slug>.html"` 解析。
- 首頁「只看收藏」用 `body.favonly` class ＋ CSS `body.favonly .card:not(.is-fav){display:none}`，與既有搜尋/標籤篩選（用 `.card[hidden]`）自然疊加，不改既有篩選 JS。
- 後端未設定（`isReady()` false）→ favorites.js 先隱藏 `#favonly` 再 return，不掛 ❤。
- 未登入點 ❤ → `signInWithGoogle()`。
- `web/firebase-config.js`（真實金鑰）維持 gitignored、永不 commit；只動 `firestore.rules`、`favorites.*`、`menu.py`、`pwa.py`、測試。
- 規則新區塊與既有 `match /games/{slug}/...` 同層，置於 `match /databases/{database}/documents` 內。

---

### Task 1: Firestore 規則 — 收藏（私有）

**Files:**
- Modify: `web/firestore.rules`

**Interfaces:**
- Produces: Firestore 對 `users/{uid}/favorites/{slug}` 的私有讀寫權限（前端 Task 2 據此讀寫）。

- [ ] **Step 1: 在 `match /databases/{database}/documents` 內、與 `match /games/{slug}/...` 同層新增**

打開 `web/firestore.rules`，找到最後一個 `match /games/{slug}/ratings/{uid} { ... }` 區塊的結尾 `}`（它在 `match /databases/{database}/documents` 之內）。在它之後、同層加入：

```
      // 收藏：完全私有，只有本人能讀寫；欄位只允許 addedAt（刪除時 request.resource.data 為 null）。
      match /users/{uid}/favorites/{slug} {
        allow read: if request.auth != null && request.auth.uid == uid;
        allow write: if request.auth != null && request.auth.uid == uid
          && (request.resource.data == null
              || request.resource.data.keys().hasOnly(['addedAt']));
      }
```

（只新增；既有 games 規則不動。確認大括號層級：此 match 與 games 同層，仍在 `match /databases/{database}/documents` 內。）

- [ ] **Step 2: 確認（無自動測試；正式驗證在規則模擬器/手動）**

Run: `grep -nE "match /users/\{uid\}/favorites" web/firestore.rules`
Expected: 顯示 `match /users/{uid}/favorites/{slug} {`。

- [ ] **Step 3: Commit**

```bash
git add web/firestore.rules
git commit -m "feat(rules): 收藏私有規則（users/{uid}/favorites）"
```

---

### Task 2: 前端模組 `web/favorites.js` ＋ `web/favorites.css`

**Files:**
- Create: `web/favorites.js`
- Create: `web/favorites.css`

**Interfaces:**
- Consumes: `./account.js` 匯出 `db, isReady, currentUser, onAuthChange, signInWithGoogle`；Firebase 9.23.0 gstatic 模組 `collection, doc, getDocs, setDoc, deleteDoc, serverTimestamp`；DOM：首頁 `#grid .card`（`href="play-<slug>.html"`）、`#favonly`；遊戲頁 `#fav-btn` 與 `window.__WT.slug`。
- Produces: 自啟動模組，無對外函式。

- [ ] **Step 1: 建立 `web/favorites.css`**

```css
/* 遊戲收藏 ❤ */
/* 首頁卡片角落的 ❤ */
.card .fav-btn-card {
  position: absolute; top: 6px; right: 6px; z-index: 2;
  background: rgba(0,0,0,.5); border: none; border-radius: 50%;
  width: 28px; height: 28px; font-size: 15px; line-height: 1;
  color: #fff; cursor: pointer; padding: 0;
}
.card .fav-btn-card.on { color: #f87171; }
/* 遊戲頁左上 ❤（基底樣式沿用 #saveui button） */
#saveui #fav-btn.on { color: #f87171; }
/* 首頁「只看收藏」鈕 */
#favonly { padding: 4px 10px; border-radius: 999px; border: 1px solid #3a3a3a;
  background: #1f2937; color: #cbd5e1; font-size: 13px; cursor: pointer; }
#favonly.active { background: #2563eb; color: #fff; border-color: #2563eb; }
```

- [ ] **Step 2: 建立 `web/favorites.js`（完整內容）**

```javascript
// 遊戲收藏：首頁卡片 ❤ + 「只看收藏」篩選；遊戲頁左上 ❤。依賴地基 account.js。
import {
  collection, doc, getDocs, setDoc, deleteDoc, serverTimestamp,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, signInWithGoogle,
} from './account.js';

const favOnlyBtn = document.getElementById('favonly');
if (!isReady()) {
  if (favOnlyBtn) favOnlyBtn.hidden = true; // 後端未設定 → 不留死鈕
} else {
  init();
}

function init() {
  const favs = new Set();          // 目前使用者已收藏的 slug
  const grid = document.getElementById('grid');
  const favBtn = document.getElementById('fav-btn');   // 遊戲頁單顆 ❤
  const favOnly = document.getElementById('favonly');  // 首頁「只看收藏」
  const cardBtns = new Map();      // slug -> 卡片上的 ❤ button
  const cardEls = new Map();       // slug -> 卡片元素

  // 首頁：每張卡片塞一顆 ❤
  if (grid) {
    grid.querySelectorAll('.card').forEach((card) => {
      const m = (card.getAttribute('href') || '').match(/^play-(.+)\.html$/);
      if (!m) return;
      const slug = m[1];
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'fav-btn-card'; b.textContent = '♡'; b.title = '收藏';
      b.onclick = (e) => { e.preventDefault(); e.stopPropagation(); toggleFav(slug); };
      card.appendChild(b);
      cardBtns.set(slug, b);
      cardEls.set(slug, card);
    });
  }

  // 首頁：「只看收藏」切換
  if (favOnly) {
    favOnly.onclick = () => {
      const on = document.body.classList.toggle('favonly');
      favOnly.classList.toggle('active', on);
    };
  }

  // 遊戲頁：單顆 ❤
  if (favBtn) {
    const slug = (window.__WT && window.__WT.slug) || '';
    favBtn.onclick = () => { if (slug) toggleFav(slug); };
  }

  function renderOne(slug) {
    const on = favs.has(slug);
    const cb = cardBtns.get(slug);
    if (cb) { cb.textContent = on ? '♥' : '♡'; cb.classList.toggle('on', on); }
    const card = cardEls.get(slug);
    if (card) card.classList.toggle('is-fav', on);
    if (favBtn && window.__WT && window.__WT.slug === slug) {
      favBtn.textContent = on ? '♥' : '♡'; favBtn.classList.toggle('on', on);
    }
  }
  function renderAll() {
    cardEls.forEach((card, slug) => renderOne(slug));
    if (favBtn && window.__WT && window.__WT.slug) renderOne(window.__WT.slug);
  }
  async function loadFavs() {
    favs.clear();
    const u = currentUser();
    if (u) {
      try {
        const snap = await getDocs(collection(db, 'users', u.uid, 'favorites'));
        snap.forEach((d) => favs.add(d.id));
      } catch (e) { /* 讀失敗 → 留空 */ }
    }
    renderAll();
  }
  async function toggleFav(slug) {
    const u = currentUser();
    if (!u) { signInWithGoogle().catch(() => alert('登入失敗')); return; }
    const was = favs.has(slug);
    if (was) favs.delete(slug); else favs.add(slug); // 樂觀更新
    renderOne(slug);
    try {
      const ref = doc(db, 'users', u.uid, 'favorites', slug);
      if (was) await deleteDoc(ref);
      else await setDoc(ref, { addedAt: serverTimestamp() });
    } catch (e) {
      if (was) favs.add(slug); else favs.delete(slug); // 還原
      renderOne(slug);
      alert('收藏失敗，請稍後再試');
    }
  }

  onAuthChange(loadFavs); // 登入/登出都重載收藏狀態
}
```

- [ ] **Step 3: 語法檢查**

Run: `cp web/favorites.js _check.mjs && node --check _check.mjs && rm _check.mjs`
Expected: 無輸出（語法正確）。

- [ ] **Step 4: Commit**

```bash
git add web/favorites.js web/favorites.css
git commit -m "feat(web): 收藏模組 favorites.js/css（首頁卡片＋遊戲頁 ❤）"
```

---

### Task 3: `menu.py` 注入首頁收藏 UI ＋ 測試

**Files:**
- Modify: `menu.py`（`_PAGE` 模板：`<style>`、工具列、`<head>`/`<body>` 腳本）
- Test: `tests/test_menu.py`

**Interfaces:**
- Consumes: `web/favorites.js`/`web/favorites.css`（Task 2；由 `install_web_assets` 自動複製）。
- Produces: 首頁含 `#favonly` 鈕、`body.favonly` CSS、`.card{position:relative}`、favorites.css/js 引用。

- [ ] **Step 1: 寫失敗測試**

在 `tests/test_menu.py` 末尾加：

```python
def test_write_menu_injects_favorites(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    entries = [{"label": "甲", "slug": "g", "cover_rel": None}]
    html = menu.write_menu(dist, "庫", entries).read_text(encoding="utf-8")
    # 「只看收藏」鈕 + 收藏篩選 CSS + 卡片定位 + 資產引用
    assert 'id="favonly"' in html
    assert "body.favonly .card:not(.is-fav)" in html
    assert "position:relative" in html
    assert 'href="favorites.css"' in html
    assert 'type="module" src="favorites.js"' in html
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_menu.py::test_write_menu_injects_favorites -v`
Expected: FAIL（尚未注入）。

- [ ] **Step 3: 在 `_PAGE` 的 `<style>` 末尾（`</style>` 之前）加兩段 CSS**

`menu.py` 的 `_PAGE` 模板裡有唯一一個 `</style>`（約第 71 行，前一行是 `.card .tag.active { background:#2563eb; color:#fff; }`）。在這個 `</style>` 之前加入兩條規則：

找到：

```
.card .tag.active { background:#2563eb; color:#fff; }
</style>
```

改成：

```
.card .tag.active { background:#2563eb; color:#fff; }
.card { position:relative; }
body.favonly .card:not(.is-fav) { display:none; }
</style>
```

（`.card` 補 `position:relative` 讓卡片角落的 ❤ 絕對定位有依據；favonly 規則讓「只看收藏」與既有 `.card[hidden]` 篩選自然疊加。）

（`.card` 補 `position:relative` 讓卡片角落的 ❤ 絕對定位有依據；favonly 規則讓「只看收藏」與既有 `.card[hidden]` 篩選自然疊加。）

- [ ] **Step 4: 在工具列加「只看收藏」鈕**

找到 `_PAGE` 內（約第 77 行）：

```html
<div class="tags" id="tagbar">__TAGFILTERS__<button id="clear">清除篩選</button></div>
</div>
```

改成（在工具列關閉 `</div>` 前加入 favonly 鈕）：

```html
<div class="tags" id="tagbar">__TAGFILTERS__<button id="clear">清除篩選</button></div>
<button id="favonly">❤ 只看收藏</button>
</div>
```

- [ ] **Step 5: 載入 favorites.css/js**

找到 `_PAGE` 模板的 `</head>`（約第 72 行），在它前面加入 css 連結：

```html
<link rel="stylesheet" href="favorites.css">
</head>
```

再找到 `_PAGE` 模板的 `</body>`（約第 135 行），在它前面加入 module 腳本：

```html
<script type="module" src="favorites.js"></script>
</body>
```

- [ ] **Step 6: 跑測試確認通過**

Run: `python -m pytest tests/test_menu.py -v`
Expected: PASS（含新測試與既有 menu 測試）。

- [ ] **Step 7: Commit**

```bash
git add menu.py tests/test_menu.py
git commit -m "feat(menu): 首頁注入收藏 ❤＋只看收藏篩選"
```

---

### Task 4: `pwa.py` 注入遊戲頁 ❤ ＋ 資產，並補 Python 測試

**Files:**
- Modify: `pwa.py`（`_SAVE_UI` 的 `#saveui` 按鈕列；新增 `_FAV_SNIPPET`；`write_game_pages` 的 `body_add`）
- Test: `tests/test_pwa_gamepages.py`、`tests/test_pwa_webassets.py`

**Interfaces:**
- Consumes: `web/favorites.js`/`web/favorites.css`（Task 2；`install_web_assets` 自動複製所有 `web/*.js`/`*.css`）。
- Produces: 每遊戲頁 `#saveui` 內 `<button id="fav-btn">`＋favorites.css/js 引用。

- [ ] **Step 1: 寫失敗測試（注入）**

在 `tests/test_pwa_gamepages.py` 末尾加：

```python
def test_write_game_pages_injects_favorite(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    pwa.write_game_pages(dist, [{"label": "甲遊戲", "slug": "g1", "cover_rel": None}])
    html = (dist / "play-g1.html").read_text(encoding="utf-8")
    assert 'id="fav-btn"' in html
    assert 'href="favorites.css"' in html
    assert 'type="module" src="favorites.js"' in html
```

- [ ] **Step 2: 寫失敗測試（資產複製）**

在 `tests/test_pwa_webassets.py` 的 `test_install_web_assets_copies_js_css` 內，把名稱元組擴充。將：

```python
    for name in ("account.js", "walkthrough.js", "walkthrough.css",
                 "community.js", "community.css"):
        assert (dist / name).exists(), name
        assert name in copied
```

改成：

```python
    for name in ("account.js", "walkthrough.js", "walkthrough.css",
                 "community.js", "community.css",
                 "favorites.js", "favorites.css"):
        assert (dist / name).exists(), name
        assert name in copied
```

- [ ] **Step 3: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_gamepages.py::test_write_game_pages_injects_favorite tests/test_pwa_webassets.py -v`
Expected: 注入測試 FAIL（尚未注入 `fav-btn`）。資產測試此時應已 PASS（favorites.* 在 Task 2 已建立、被自動複製）。

- [ ] **Step 4: 在 `_SAVE_UI` 按鈕列加 ❤**

在 `pwa.py` 找到（約第 191 行）：

```html
<div id="saveui"><button id="wt-open">攻略</button><button id="cm-open">留言</button><button id="saveexp">導出存檔</button><button id="saveimp">導入存檔</button>
```

改成（在「留言」之後加 ❤）：

```html
<div id="saveui"><button id="wt-open">攻略</button><button id="cm-open">留言</button><button id="fav-btn" title="收藏">♡</button><button id="saveexp">導出存檔</button><button id="saveimp">導入存檔</button>
```

- [ ] **Step 5: 新增 `_FAV_SNIPPET` 並接到 `body_add`**

在 `pwa.py` 的 `_CM_SNIPPET = """..."""` 定義之後，新增：

```python
# 收藏：純前端模組（讀 _WT_SNIPPET 注入的 window.__WT.slug；同一支也處理首頁卡片）。
_FAV_SNIPPET = """
<link rel="stylesheet" href="favorites.css">
<script type="module" src="favorites.js"></script>
"""
```

接著找到（約第 397 行）：

```python
        body_add = dl_snippet + save_snippet + wt_snippet + _CM_SNIPPET
```

改成：

```python
        body_add = dl_snippet + save_snippet + wt_snippet + _CM_SNIPPET + _FAV_SNIPPET
```

- [ ] **Step 6: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_gamepages.py tests/test_pwa_webassets.py -v`
Expected: PASS。

- [ ] **Step 7: 全測試**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS。

- [ ] **Step 8: Commit**

```bash
git add pwa.py tests/test_pwa_gamepages.py tests/test_pwa_webassets.py
git commit -m "feat(pwa): 遊戲頁注入收藏 ❤＋favorites 資產"
```

---

## 收尾：手動驗證（非自動測試）

- [ ] 重建並部署，且 Firestore 規則**重新發布**（本輪規則為擴充，須一併發布）。
- [ ] 登入→首頁卡片角落點 ❤ 收藏一個（變實心）→「❤ 只看收藏」只剩它（搭配標籤/搜尋仍正確）→進該遊戲頁，左上 ❤ 同步顯示已收藏→取消收藏→兩處同步。
- [ ] 換另一個 Google 帳號→看不到你的收藏（私有）。
- [ ] 未登入點 ❤→觸發登入；firebase-config 仍佔位→首頁不顯示「只看收藏」、無 ❤。

## Self-Review 註記（已檢查）

- **Spec 覆蓋**：資料模型/私有規則(Task1)、favorites.js 首頁卡片＋遊戲頁雙情境/樂觀更新/onAuthChange(Task2)、favonly 篩選與既有篩選疊加(Task2 CSS class + Task3 CSS)、首頁注入(Task3)、遊戲頁注入＋資產(Task4)、isReady 隱藏 #favonly(Task2)、未登入觸發登入(Task2)——皆有對應任務。
- **型別一致**：`window.__WT.slug`、`#grid .card[href]`、`#favonly`、`#fav-btn` 在 Task2 使用與 Task3/Task4 注入的元素 id/結構一致；favorites 欄位 `{addedAt}` 與規則 `hasOnly(['addedAt'])` 一致；doc id＝slug 與 `users/{uid}/favorites/{slug}` 一致；`account.js` 匯出與既有 walkthrough/community 用法一致（新用 `setDoc`/`deleteDoc`/`collection`/`getDocs`/`serverTimestamp`）。
- **非自動測試**：Firestore 規則與 ❤ 互動屬瀏覽器端，靠收尾手動驗；Python 測涵蓋首頁/遊戲頁注入與資產複製；JS 靠 node --check。
