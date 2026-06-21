# 個人頁 profile.html Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 新增獨立的個人頁 `profile.html`，登入後顯示「我的收藏」與「最近遊玩（含已遊玩時間）」，首頁加「👤 我的」連結。

**Architecture:** build 新增 `menu.write_profile()` 產 `profile.html`（嵌入 `window.__GAMES` 遊戲清單），由 `web/profile.js` 讀 `users/<uid>/{favorites,history}`（既有私有資料、規則已放行，**不改規則**）渲染卡片。`profile.js`/`profile.css` 由 `install_web_assets` 自動複製。

**Tech Stack:** Firebase 9.23.0（gstatic CDN 模組）、純前端 ES module、Python build（menu.py/easyrpg_web_build.py）、pytest。

## Global Constraints

- 設計依據：`docs/superpowers/specs/2026-06-22-profile-page-design.md`。
- Firebase SDK 固定 `https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js`。
- **不改 `web/firestore.rules`**（只讀已放行的本人私有 favorites/history）。
- 卡片名稱用 `textContent`（無 XSS）；封面用 `img`。卡片連到 `play-<slug>.html`。
- 我的收藏依 `addedAt` 新到舊；最近遊玩依 `lastPlayedAt` 新到舊（單欄位 orderBy，免索引）。
- 找不到 `window.__GAMES[slug]`（遊戲下架）→ 略過該筆。
- `web/firebase-config.js`（真實金鑰）維持 gitignored、永不 commit；只動 `profile.*`、`menu.py`、`easyrpg_web_build.py`、測試。

---

### Task 1: 前端 `web/profile.js` ＋ `web/profile.css`

**Files:** Create `web/profile.js`, `web/profile.css`

**Interfaces:**
- Consumes: `./account.js`（`db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser`）；Firebase 模組 `collection, getDocs, query, orderBy`；DOM `#my-favs`、`#my-history`、`#me-auth`；`window.__GAMES = { slug: { label, cover } }`。

- [ ] **Step 1: 建立 `web/profile.css`**

```css
/* 個人頁 */
body { margin:0; background:#111; color:#eee;
  font-family:-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif; }
.pf-top { display:flex; align-items:center; gap:12px; padding:14px 16px; border-bottom:1px solid #2a2a2a; }
.pf-back { color:#9ca3af; text-decoration:none; font-size:14px; }
.pf-title { font-size:18px; }
.pf-auth { margin-left:auto; font-size:13px; color:#9ca3af; }
.pf-auth button { border:1px solid #3a3a3a; background:#1f2937; color:#cbd5e1;
  border-radius:8px; padding:4px 10px; font-size:13px; cursor:pointer; }
.pf-section { padding:12px 16px; }
.pf-section h2 { font-size:15px; color:#cbd5e1; margin:8px 0; }
.pf-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(110px,1fr));
  gap:14px; color:#888; }
.pf-card { display:flex; flex-direction:column; align-items:center; text-decoration:none; color:#eee; }
.pf-card img { width:100%; aspect-ratio:1/1; object-fit:cover; border-radius:12px; background:#1b1b1b; }
.pf-card .pf-name { margin-top:6px; font-size:13px; text-align:center; word-break:break-word; }
.pf-card .pf-sub { font-size:12px; color:#fbbf24; }
```

- [ ] **Step 2: 建立 `web/profile.js`（完整內容）**

```javascript
// 個人頁：顯示我的收藏與最近遊玩。讀 users/<uid>/{favorites,history}，用 window.__GAMES 渲染卡片。
import {
  collection, getDocs, query, orderBy,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser,
} from './account.js';

const GAMES = window.__GAMES || {};
const favsEl = document.getElementById('my-favs');
const histEl = document.getElementById('my-history');
const authEl = document.getElementById('me-auth');

function fmt(sec) {
  const s = Math.floor(sec || 0);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h) return h + 'h' + (m ? ' ' + m + 'm' : '');
  if (m) return m + 'm';
  return s + 's';
}
function card(slug, sub) {
  const g = GAMES[slug];
  if (!g) return null;
  const a = document.createElement('a');
  a.className = 'pf-card';
  a.href = 'play-' + slug + '.html';
  const img = document.createElement('img');
  img.src = g.cover; img.alt = '';
  a.appendChild(img);
  const name = document.createElement('span');
  name.className = 'pf-name';
  name.textContent = g.label;
  a.appendChild(name);
  if (sub) {
    const s = document.createElement('span');
    s.className = 'pf-sub'; s.textContent = sub;
    a.appendChild(s);
  }
  return a;
}

if (!isReady()) {
  favsEl.textContent = '站長尚未設定後端';
  histEl.textContent = '站長尚未設定後端';
} else {
  onAuthChange(render);
}

function render(u) {
  authEl.innerHTML = '';
  if (u) {
    authEl.append(document.createTextNode((u.displayName || '已登入') + ' '));
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = '登出';
    b.onclick = () => signOutUser();
    authEl.append(b);
    loadFavs(u.uid);
    loadHistory(u.uid);
  } else {
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = '用 Google 登入';
    b.onclick = () => signInWithGoogle().catch(() => alert('登入失敗'));
    authEl.append(b);
    favsEl.textContent = '登入後可看你的收藏與遊玩紀錄';
    histEl.textContent = '';
  }
}

async function loadFavs(uid) {
  favsEl.textContent = '載入中…';
  try {
    const snap = await getDocs(query(
      collection(db, 'users', uid, 'favorites'), orderBy('addedAt', 'desc'),
    ));
    favsEl.innerHTML = '';
    let n = 0;
    snap.forEach((d) => { const c = card(d.id, ''); if (c) { favsEl.appendChild(c); n += 1; } });
    if (!n) favsEl.textContent = '還沒有收藏';
  } catch (e) { favsEl.textContent = '載入失敗，請稍後再試'; }
}

async function loadHistory(uid) {
  histEl.textContent = '載入中…';
  try {
    const snap = await getDocs(query(
      collection(db, 'users', uid, 'history'), orderBy('lastPlayedAt', 'desc'),
    ));
    histEl.innerHTML = '';
    let n = 0;
    snap.forEach((d) => {
      const c = card(d.id, '已遊玩 ' + fmt(d.data().totalSeconds));
      if (c) { histEl.appendChild(c); n += 1; }
    });
    if (!n) histEl.textContent = '還沒有遊玩紀錄';
  } catch (e) { histEl.textContent = '載入失敗，請稍後再試'; }
}
```

- [ ] **Step 3: 語法檢查**

Run: `cp web/profile.js _check.mjs && node --check _check.mjs && rm _check.mjs`
Expected: 無輸出。

- [ ] **Step 4: Commit**

```bash
git add web/profile.js web/profile.css
git commit -m "feat(web): 個人頁前端 profile.js/css（我的收藏＋最近遊玩）"
```

---

### Task 2: `menu.py` 產 profile.html ＋ 首頁「我的」連結，補測試

**Files:** Modify `menu.py`；Test `tests/test_menu.py`、`tests/test_pwa_webassets.py`

**Interfaces:**
- Produces: `menu.write_profile(dist, app_label, entries, icon_rel=pwa.ICON_REL) -> Path`（寫 `dist/profile.html`，含 `window.__GAMES`）。Task 3 會呼叫它。

- [ ] **Step 1: 寫失敗測試**

在 `tests/test_menu.py` 末尾加：

```python
def test_write_profile_page(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    entries = [
        {"label": "甲遊戲", "slug": "g1", "cover_rel": "games/g1/cover.png"},
        {"label": "乙", "slug": "g2", "cover_rel": None},
    ]
    out = menu.write_profile(dist, "我的庫", entries)
    assert out == dist / "profile.html"
    html = out.read_text(encoding="utf-8")
    assert "window.__GAMES" in html
    assert '"g1"' in html and "甲遊戲" in html
    assert 'id="my-favs"' in html and 'id="my-history"' in html
    assert 'href="profile.css"' in html
    assert 'type="module" src="profile.js"' in html
    assert "返回" in html


def test_write_menu_has_profile_link(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    html = menu.write_menu(dist, "庫", [{"label": "甲", "slug": "g", "cover_rel": None}]).read_text(encoding="utf-8")
    assert 'id="me-link"' in html
    assert 'href="profile.html"' in html
```

- [ ] **Step 2: 在 `tests/test_pwa_webassets.py` 補資產斷言**

把 `test_install_web_assets_copies_js_css` 的名稱元組擴充加入 `"profile.js"`, `"profile.css"`。將：

```python
    for name in ("account.js", "walkthrough.js", "walkthrough.css",
                 "community.js", "community.css",
                 "favorites.js", "favorites.css", "playtime.js"):
        assert (dist / name).exists(), name
        assert name in copied
```

改成：

```python
    for name in ("account.js", "walkthrough.js", "walkthrough.css",
                 "community.js", "community.css",
                 "favorites.js", "favorites.css", "playtime.js",
                 "profile.js", "profile.css"):
        assert (dist / name).exists(), name
        assert name in copied
```

- [ ] **Step 3: 跑測試確認失敗**

Run: `python -m pytest tests/test_menu.py::test_write_profile_page tests/test_menu.py::test_write_menu_has_profile_link tests/test_pwa_webassets.py -v`
Expected: 兩個 menu 測試 FAIL（尚無 write_profile / me-link）；webassets 測試 FAIL（尚無 profile.js/css；Task 1 已建立則此項應 PASS）。

- [ ] **Step 4: `menu.py` 加 `import json`**

把 `menu.py` 開頭：

```python
import html as _html
from pathlib import Path
```

改成：

```python
import html as _html
import json
from pathlib import Path
```

- [ ] **Step 5: `_PAGE` 加「我的」連結與樣式**

在 `menu.py` 的 `_PAGE` 模板找到（約第 71-73 行，`<style>` 結尾）：

```
body.favonly .card:not(.is-fav) { display:none; }
</style>
```

改成（在 `</style>` 前加 `#me-link` 樣式）：

```
body.favonly .card:not(.is-fav) { display:none; }
#me-link { position:fixed; top:10px; right:12px; z-index:5; text-decoration:none;
  padding:4px 10px; border-radius:999px; border:1px solid #3a3a3a;
  background:#1f2937; color:#cbd5e1; font-size:13px; }
</style>
```

再找到（`_PAGE` 的 body 開頭）：

```
<header>__TITLE__</header>
<div class="toolbar">
```

改成（在標題後加連結）：

```
<header>__TITLE__</header>
<a href="profile.html" id="me-link">👤 我的</a>
<div class="toolbar">
```

- [ ] **Step 6: 在 `_CARD` 定義之後，新增 `_PROFILE_PAGE` 與 `write_profile`**

在 `menu.py` 的 `_CARD = (...)` 區塊之後（`def write_menu` 之前）加入：

```python
_PROFILE_PAGE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>我的 · __TITLE__</title>__PWAHEAD__
<link rel="stylesheet" href="profile.css">
</head>
<body>
<div class="pf-top">
<a href="index.html" class="pf-back">← 返回遊戲庫</a>
<strong class="pf-title">我的</strong>
<span id="me-auth" class="pf-auth"></span>
</div>
<section class="pf-section"><h2>我的收藏</h2><div id="my-favs" class="pf-grid"></div></section>
<section class="pf-section"><h2>最近遊玩</h2><div id="my-history" class="pf-grid"></div></section>
__GAMES__
<script type="module" src="profile.js"></script>
</body>
</html>
"""


def write_profile(dist, app_label: str, entries, icon_rel: str = pwa.ICON_REL) -> Path:
    """產生個人頁 profile.html，嵌入 window.__GAMES（slug→{label,cover}）供 profile.js 渲染卡片。"""
    games = {
        e["slug"]: {"label": e["label"], "cover": e.get("cover_rel") or icon_rel}
        for e in entries
    }
    games_js = ("<script>window.__GAMES="
                + json.dumps(games, ensure_ascii=False).replace("<", "\\u003c")
                + ";</script>")
    page = (
        _PROFILE_PAGE.replace("__PWAHEAD__", pwa.pwa_head(app_label, icon_rel))
        .replace("__TITLE__", _html.escape(app_label))
        .replace("__GAMES__", games_js)
    )
    out = Path(dist) / "profile.html"
    out.write_text(page, encoding="utf-8")
    return out
```

- [ ] **Step 7: 跑測試確認通過**

Run: `python -m pytest tests/test_menu.py tests/test_pwa_webassets.py -v`
Expected: PASS（含新測試與既有測試）。

- [ ] **Step 8: Commit**

```bash
git add menu.py tests/test_menu.py tests/test_pwa_webassets.py
git commit -m "feat(menu): 產生個人頁 profile.html＋首頁「我的」連結"
```

---

### Task 3: `easyrpg_web_build.py` 串接 write_profile ＋ 建置測試

**Files:** Modify `easyrpg_web_build.py`；Test `tests/test_build_library.py`

**Interfaces:**
- Consumes: `menu.write_profile(out, app_label, entries, icon_rel)`（Task 2）。

- [ ] **Step 1: 在既有建置測試補斷言**

在 `tests/test_build_library.py` 的 `test_build_library_two_games` 末尾（既有斷言之後）加：

```python
    assert (out / "profile.html").exists()
    prof = (out / "profile.html").read_text(encoding="utf-8")
    assert "window.__GAMES" in prof
    assert 'id="my-favs"' in prof and 'id="my-history"' in prof
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_build_library.py::test_build_library_two_games -v`
Expected: FAIL（build 尚未產 profile.html）。

- [ ] **Step 3: 在 build_library 串接 write_profile**

在 `easyrpg_web_build.py` 找到呼叫 `menu.write_menu(...)` 的那一行（約第 181 行）：

```python
    menu.write_menu(out, app_label, entries, icon_rel,
                    tag_categories=tag_categories)
```

在它後面加一行：

```python
    menu.write_profile(out, app_label, entries, icon_rel)
```

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_build_library.py -v`
Expected: PASS。

- [ ] **Step 5: 全測試**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS。

- [ ] **Step 6: Commit**

```bash
git add easyrpg_web_build.py tests/test_build_library.py
git commit -m "feat(build): 建置時產生個人頁 profile.html"
```

---

## 收尾：手動驗證

- [ ] 重建並部署（規則不必重發，除非之前未發布收藏/紀錄規則）。
- [ ] 首頁右上「👤 我的」→ 個人頁；未登入顯示登入提示。
- [ ] 登入後：我的收藏（封面/名稱、點進遊戲）、最近遊玩（含「已遊玩 Xh Ym」、依最近排序）。
- [ ] 「← 返回遊戲庫」回首頁。換另一帳號看到自己的資料。空清單顯示友善提示。

## Self-Review 註記（已檢查）
- **Spec 覆蓋**：write_profile 產頁＋嵌 __GAMES(Task2)、首頁我的連結(Task2)、build 串接(Task3)、profile.js 兩區塊/登入/空清單/錯誤(Task1)、資產複製(Task2 webassets 斷言)、不改規則——皆有對應。
- **型別一致**：`window.__GAMES`(slug→{label,cover}) 由 write_profile 寫、profile.js 讀，鍵名一致；`#my-favs`/`#my-history`/`#me-auth` 在模板與 profile.js 一致；卡片連結 `play-<slug>.html`；favorites 欄位 addedAt、history 欄位 totalSeconds/lastPlayedAt 與既有寫入一致；orderBy 單欄位免索引。
- **無 placeholder**：各步含完整程式碼／測試／指令與預期。
