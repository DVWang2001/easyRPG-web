# 遊玩次數＋熱門排行 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 開遊戲頁時 `stats/<slug>.plays` +1（每瀏覽器每遊戲每天一次）；首頁卡片顯遊玩次數，工具列「🔥 熱門」鈕依次數重排。

**Architecture:** 公開計數存 Firestore `stats/<slug>{plays}`（規則限 +1）。新模組 `web/popular.js` 一支兩用：遊戲頁計數、首頁讀次數＋排序。`menu.py`/`pwa.py` 分別注入首頁/遊戲頁。

**Tech Stack:** Firebase 9.23.0（gstatic CDN，`increment`）、純前端 ES module、Python build、pytest。

## Global Constraints

- 設計依據：`docs/superpowers/specs/2026-06-22-popular-ranking-design.md`。
- Firebase SDK 固定 `https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js`。
- 公開計數：`stats/<slug>` 公開可讀；寫入限「`plays` 恰 +1、`hasOnly(['plays'])`」；不需登入；不允許刪除。
- 計數去重：每瀏覽器每遊戲每天一次（localStorage key `ep-pl-<slug>` 存 `YYYY-MM-DD`）。
- 首頁卡片 slug 從 `href="play-<slug>.html"` 解析；次數 > 0 才顯「▶ N」badge。
- `!isReady()` → 不計數、首頁隱藏 `#hot`、不顯次數。
- 「🔥 熱門」與既有搜尋/標籤隱藏並存（只重排 DOM，不改既有篩選 JS）。
- `web/firebase-config.js`（真實金鑰）維持 gitignored、永不 commit；只動 `firestore.rules`、`popular.*`、`menu.py`、`pwa.py`、測試。

---

### Task 1: Firestore 規則 — 公開遊玩次數

**Files:** Modify `web/firestore.rules`

- [ ] **Step 1: 在 `match /databases/{database}/documents` 內、與 `match /games/{slug}` 同層新增**

找到 `match /games/{slug}/walkthroughs/{id}` 區塊之前（或 `match /users/{uid}/...` 之後，任一同層位置），在 `match /databases/{database}/documents {` 內加入：

```
      // 遊玩次數：公開可讀；任何人可把 plays +1（無其他欄位），不需登入；不允許刪除。
      match /stats/{slug} {
        allow read: if true;
        allow create: if request.resource.data.keys().hasOnly(['plays'])
          && request.resource.data.plays == 1;
        allow update: if request.resource.data.keys().hasOnly(['plays'])
          && request.resource.data.plays == resource.data.plays + 1;
      }
```

（只新增；既有規則不動。確認大括號層級與 `match /games/{slug}/...`、`match /users/{uid}/...` 同層，仍在 `match /databases/{database}/documents` 內。）

- [ ] **Step 2: 確認**

Run: `grep -nE "match /stats/\{slug\}" web/firestore.rules`
Expected: 顯示 `match /stats/{slug} {`。

- [ ] **Step 3: Commit**

```bash
git add web/firestore.rules
git commit -m "feat(rules): 公開遊玩次數規則（stats/{slug}，plays 限 +1）"
```

---

### Task 2: 前端 `web/popular.js` ＋ `web/popular.css`

**Files:** Create `web/popular.js`, `web/popular.css`

**Interfaces:**
- Consumes: `./account.js`（`db, isReady`）；Firebase `doc, collection, getDocs, setDoc, increment`；DOM 首頁 `#grid .card`、`#hot`；遊戲頁 `window.__WT.slug`。

- [ ] **Step 1: 建立 `web/popular.css`**

```css
/* 熱門：遊玩次數 badge ＋ 排序鈕 */
.card .play-badge { position:absolute; left:6px; top:6px; z-index:2;
  background:rgba(0,0,0,.6); color:#fff; font-size:11px; padding:1px 6px; border-radius:999px; }
#hot { padding:4px 10px; border-radius:999px; border:1px solid #3a3a3a;
  background:#1f2937; color:#cbd5e1; font-size:13px; cursor:pointer; }
#hot.active { background:#dc2626; color:#fff; border-color:#dc2626; }
```

- [ ] **Step 2: 建立 `web/popular.js`（完整內容）**

```javascript
// 熱門：開遊戲頁計數（stats/<slug>.plays +1，每瀏覽器每遊戲每天一次）；首頁顯次數＋「🔥 熱門」排序。
import {
  doc, collection, getDocs, setDoc, increment,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import { db, isReady } from './account.js';

const hotBtn = document.getElementById('hot');
if (!isReady()) {
  if (hotBtn) hotBtn.hidden = true; // 後端未設定 → 不留無效鈕
} else {
  const grid = document.getElementById('grid');
  const SLUG = (window.__WT && window.__WT.slug) || '';
  if (grid) initHome(grid);
  else if (SLUG) countPlay(SLUG);
}

async function countPlay(slug) {
  const key = 'ep-pl-' + slug;
  const today = new Date().toISOString().slice(0, 10);
  if (localStorage.getItem(key) === today) return;
  try {
    await setDoc(doc(db, 'stats', slug), { plays: increment(1) }, { merge: true });
    localStorage.setItem(key, today);
  } catch (e) { /* 安靜略過，下次再試 */ }
}

function slugOf(card) {
  const m = (card.getAttribute('href') || '').match(/^play-(.+)\.html$/);
  return m ? m[1] : '';
}

function initHome(grid) {
  const cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
  const order = cards.slice(); // 原始順序
  const plays = {};

  const hot = document.getElementById('hot');
  if (hot) hot.onclick = () => {
    const on = !hot.classList.contains('active');
    hot.classList.toggle('active', on);
    const seq = on
      ? cards.slice().sort((a, b) => ((plays[slugOf(b)] || 0) - (plays[slugOf(a)] || 0))
          || (order.indexOf(a) - order.indexOf(b)))
      : order;
    seq.forEach((c) => grid.appendChild(c));
  };

  getDocs(collection(db, 'stats')).then((snap) => {
    snap.forEach((d) => { const p = d.data().plays; if (typeof p === 'number') plays[d.id] = p; });
    cards.forEach((c) => {
      const n = plays[slugOf(c)] || 0;
      if (n > 0) {
        const b = document.createElement('span');
        b.className = 'play-badge';
        b.textContent = '▶ ' + n;
        c.appendChild(b);
      }
    });
  }).catch(() => {});
}
```

- [ ] **Step 3: 語法檢查**

Run: `cp web/popular.js _check.mjs && node --check _check.mjs && rm _check.mjs`
Expected: 無輸出。

- [ ] **Step 4: Commit**

```bash
git add web/popular.js web/popular.css
git commit -m "feat(web): 熱門模組 popular.js/css（計數＋首頁次數/排序）"
```

---

### Task 3: `menu.py` 首頁注入「🔥 熱門」＋ popular 資產，補測試

**Files:** Modify `menu.py`；Test `tests/test_menu.py`、`tests/test_pwa_webassets.py`

- [ ] **Step 1: 寫失敗測試**

在 `tests/test_menu.py` 末尾加：

```python
def test_write_menu_has_hot_button(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    html = menu.write_menu(dist, "庫", [{"label": "甲", "slug": "g", "cover_rel": None}]).read_text(encoding="utf-8")
    assert 'id="hot"' in html
    assert 'href="popular.css"' in html
    assert 'type="module" src="popular.js"' in html
```

- [ ] **Step 2: 在 `tests/test_pwa_webassets.py` 補資產斷言**

把 `test_install_web_assets_copies_js_css` 的名稱元組擴充加入 `"popular.js"`, `"popular.css"`。將：

```python
                 "profile.js", "profile.css",
                 "savepanel.js", "savepanel.css"):
```

改成：

```python
                 "profile.js", "profile.css",
                 "savepanel.js", "savepanel.css",
                 "popular.js", "popular.css"):
```

- [ ] **Step 3: 跑測試確認失敗**

Run: `python -m pytest tests/test_menu.py::test_write_menu_has_hot_button tests/test_pwa_webassets.py -q`
Expected: menu 測試 FAIL；webassets 此時應已 PASS（Task 2 已建立 popular.*）。

- [ ] **Step 4: `_PAGE` 工具列加「🔥 熱門」鈕**

在 `menu.py` 的 `_PAGE` 找到：

```html
<button id="favonly">❤ 只看收藏</button>
</div>
```

改成（在 favonly 之後加 hot）：

```html
<button id="favonly">❤ 只看收藏</button>
<button id="hot">🔥 熱門</button>
</div>
```

- [ ] **Step 5: 載入 popular.css/js**

找到 `_PAGE` 的 `<link rel="stylesheet" href="favorites.css">`，在其後加：

```html
<link rel="stylesheet" href="favorites.css">
<link rel="stylesheet" href="popular.css">
```

找到 `_PAGE` 的 `<script type="module" src="favorites.js"></script>`，在其後加：

```html
<script type="module" src="favorites.js"></script>
<script type="module" src="popular.js"></script>
```

- [ ] **Step 6: 跑測試確認通過**

Run: `python -m pytest tests/test_menu.py tests/test_pwa_webassets.py -q`
Expected: PASS。

- [ ] **Step 7: Commit**

```bash
git add menu.py tests/test_menu.py tests/test_pwa_webassets.py
git commit -m "feat(menu): 首頁注入「🔥 熱門」排序＋popular 資產"
```

---

### Task 4: `pwa.py` 遊戲頁注入 popular.js（計數），補測試

**Files:** Modify `pwa.py`；Test `tests/test_pwa_gamepages.py`

- [ ] **Step 1: 寫失敗測試**

在 `tests/test_pwa_gamepages.py` 末尾加：

```python
def test_write_game_pages_injects_popular(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    pwa.write_game_pages(dist, [{"label": "甲", "slug": "g", "cover_rel": None}])
    html = (dist / "play-g.html").read_text(encoding="utf-8")
    assert 'type="module" src="popular.js"' in html
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_gamepages.py::test_write_game_pages_injects_popular -q`
Expected: FAIL。

- [ ] **Step 3: 新增 `_POP_SNIPPET` 並接到 `body_add`**

在 `pwa.py` 的 `_FS_FALLBACK = r"""..."""` 定義之後，新增：

```python
# 熱門：純前端模組（開遊戲頁計數 stats/<slug>；同一支也處理首頁排序）。
_POP_SNIPPET = """
<script type="module" src="popular.js"></script>
"""
```

找到（cloud/fullscreen 完成後的版本）：

```python
        body_add = dl_snippet + save_snippet + wt_snippet + _CM_SNIPPET + _FAV_SNIPPET + _PT_SNIPPET + _CLOUD_SNIPPET + _FS_FALLBACK
```

改成：

```python
        body_add = dl_snippet + save_snippet + wt_snippet + _CM_SNIPPET + _FAV_SNIPPET + _PT_SNIPPET + _CLOUD_SNIPPET + _FS_FALLBACK + _POP_SNIPPET
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_pwa_gamepages.py -q`
Expected: PASS。

- [ ] **Step 5: 全測試**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS。

- [ ] **Step 6: Commit**

```bash
git add pwa.py tests/test_pwa_gamepages.py
git commit -m "feat(pwa): 遊戲頁注入 popular.js（遊玩次數計數）"
```

---

## 收尾：手動驗證

- [ ] 重建並部署，且 Firestore 規則**重新發布**（本輪規則為擴充）。
- [ ] 開幾個遊戲頁（不同遊戲）→ 回首頁，卡片角落出現「▶ 次數」。
- [ ] 工具列「🔥 熱門」→ 依次數高到低重排；再按還原；搭配搜尋/標籤篩選仍正確。
- [ ] 同瀏覽器當天重開同一遊戲不重複計（隔天才再 +1）。
- [ ] firebase-config 仍佔位→首頁無「🔥 熱門」鈕、無次數。

## Self-Review 註記（已檢查）
- **Spec 覆蓋**：公開規則(Task1)、popular.js 計數/去重/首頁次數/排序/!isReady(Task2)、首頁注入(Task3)、遊戲頁注入計數(Task4)、資產複製(Task3 webassets)——皆有對應。
- **型別一致**：`stats/<slug>{plays}` 寫(increment)與讀(d.data().plays)、規則 hasOnly(['plays']) 一致；`#hot`/`#grid .card[href]`/`window.__WT.slug` 與注入端一致；slug 解析 `^play-(.+)\.html$` 與 favorites 同手法。
- **不破壞既有篩選**：popular 只重排 DOM、加 badge，不改 menu.py 既有篩選 inline JS。
