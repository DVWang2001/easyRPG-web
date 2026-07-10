# 玩家端觸控按鍵編輯器 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 玩家在手機瀏覽器內拖拉編輯遊戲頁觸控按鍵（新增 0–9／Shift、移位、移除、還原），逐遊戲逐裝置存 localStorage。

**Architecture:** 兩支新 JS：`web/touchlayout.js`（純邏輯：佈局驗證＋盤面定義，node 可測）與 `web/touchpad.js`（DOM：套用佈局、自訂鍵派發、編輯模式 UI，全部動態建立）。建置端唯一改動＝`pwa.py` 加一行 `_TP_SNIPPET`。自訂鍵掛在 `#apad` 下繼承 vendor 圓鈕樣式與「觸控顯示／手把隱藏」；按鍵語意＝對 `#canvas` 派發 keydown/keyup（同 vendor `simulateKeyboardEvent`）。

**Tech Stack:** 原生 JS module（零相依）；pytest（建置端字串斷言）；`node --test`（純函式）。

**Spec:** `docs/superpowers/specs/2026-07-10-player-touch-editor-design.md`

## Global Constraints

- 不新增任何相依；不新增 css 檔（樣式由 touchpad.js 注入）；不改 `_SAVE_UI`。
- localStorage key：`ep-touch-<slug>`；格式 `{"v":1,"buttons":[…]}`；x/y＝視窗百分比，夾限 **0–95**。
- 內建鍵 id 固定五個：`dpad`、`apad-escape`、`apad-enter`、`apad-ff3`、`apad-ff10`。
- 自訂鍵只允許盤面鍵：`ShiftLeft`、`Digit0`…`Digit9`（決定/取消/»/»» 由內建鍵 chips 提供，不重複做成自訂鍵）。
- **沒有紀錄＝完全不動 vendor 預設**；有紀錄＝清單未列的內建鍵隱藏。
- 自訂鍵插在 `apad-escape` 之前（保住 vendor `:last-child` 的 Enter 定位）。
- 入口鈕僅 `(hover: none), (pointer: coarse)` 顯示；編輯模式用 `window.__epPause(true,'tp')` 暫停遊戲。
- 工作分支：`feat/touch-editor`（從 main 建）。每個 commit 只 add 該任務點名的檔案。
- 測試指令：`python -m pytest tests/ -q`（已知 pre-existing 失敗：`test_menu.py::test_write_menu_injects_announcements`，與本功能無關）；`node --test tests/test_touchlayout.mjs`。

## File Structure

| 檔案 | 動作 | 責任 |
|---|---|---|
| `web/touchlayout.js` | 新增 | 純邏輯：`normalizeLayout`、`PALETTE`、`BUILTIN_IDS`（node 可測、零 DOM） |
| `tests/test_touchlayout.mjs` | 新增 | `normalizeLayout` 的 node --test |
| `web/touchpad.js` | 新增 | DOM：佈局套用＋自訂鍵派發（Task 2）＋編輯模式（Task 3） |
| `pwa.py` | 修改 | `_TP_SNIPPET` 加進 `body_add` |
| `tests/test_pwa_gamepages.py` | 修改 | 斷言遊戲頁含 touchpad.js |

---

### Task 1: `touchlayout.js` 純邏輯＋node 測試

**Files:**
- Create: `web/touchlayout.js`
- Test: `tests/test_touchlayout.mjs`

**Interfaces:**
- Produces:
  - `normalizeLayout(raw) → {v:1, buttons:[{id,x,y}|{key,label,x,y}]} | null`（raw＝JSON.parse 後任意值；null＝壞資料當沒紀錄）
  - `PALETTE: [{key,label}]`＝`ShiftLeft`＋`Digit0`…`Digit9`（label：'Shift'、'0'…'9'）
  - `BUILTIN_IDS: string[]`＝上列五個內建 id
- Task 2/3 以 `import { normalizeLayout, PALETTE, BUILTIN_IDS } from './touchlayout.js'` 消費。

- [ ] **Step 1: 開分支**

```powershell
git checkout -b feat/touch-editor
```

- [ ] **Step 2: 寫失敗測試 `tests/test_touchlayout.mjs`**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeLayout, PALETTE, BUILTIN_IDS } from '../web/touchlayout.js';

test('盤面＝Shift＋0–9，共 11 鍵', () => {
  assert.equal(PALETTE.length, 11);
  assert.deepEqual(PALETTE[0], { key: 'ShiftLeft', label: 'Shift' });
  assert.deepEqual(PALETTE[10], { key: 'Digit9', label: '9' });
});

test('內建 id 固定五個', () => {
  assert.deepEqual(BUILTIN_IDS,
    ['dpad', 'apad-escape', 'apad-enter', 'apad-ff3', 'apad-ff10']);
});

test('合法輸入原樣通過', () => {
  const r = normalizeLayout({ v: 1, buttons: [
    { id: 'dpad', x: 2, y: 60 },
    { key: 'Digit1', label: '1', x: 52, y: 88 },
  ] });
  assert.deepEqual(r, { v: 1, buttons: [
    { id: 'dpad', x: 2, y: 60 },
    { key: 'Digit1', label: '1', x: 52, y: 88 },
  ] });
});

test('非物件／缺 buttons → null', () => {
  assert.equal(normalizeLayout(null), null);
  assert.equal(normalizeLayout('x'), null);
  assert.equal(normalizeLayout({ v: 1 }), null);
  assert.equal(normalizeLayout({ buttons: 'x' }), null);
});

test('空 buttons 合法（＝全部隱藏）', () => {
  assert.deepEqual(normalizeLayout({ v: 1, buttons: [] }), { v: 1, buttons: [] });
});

test('壞項被丟：未知 id、未知 key、非數字座標', () => {
  const r = normalizeLayout({ v: 1, buttons: [
    { id: 'hack', x: 1, y: 1 },
    { key: 'KeyZ', label: 'Z', x: 1, y: 1 },
    { key: 'Digit1', label: '1', x: 'a', y: 1 },
    { id: 'dpad', x: 3, y: 4 },
  ] });
  assert.deepEqual(r.buttons, [{ id: 'dpad', x: 3, y: 4 }]);
});

test('座標夾限 0–95', () => {
  const r = normalizeLayout({ v: 1, buttons: [{ id: 'dpad', x: -5, y: 120 }] });
  assert.deepEqual(r.buttons, [{ id: 'dpad', x: 0, y: 95 }]);
});

test('重複 id/key 取第一個', () => {
  const r = normalizeLayout({ v: 1, buttons: [
    { id: 'dpad', x: 1, y: 1 }, { id: 'dpad', x: 9, y: 9 },
    { key: 'Digit1', x: 2, y: 2 }, { key: 'Digit1', x: 8, y: 8 },
  ] });
  assert.equal(r.buttons.length, 2);
  assert.equal(r.buttons[0].x, 1);
  assert.equal(r.buttons[1].x, 2);
});

test('label 一律以盤面為準（存壞了也矯正）', () => {
  const r = normalizeLayout({ v: 1, buttons: [{ key: 'ShiftLeft', label: '<img>', x: 1, y: 1 }] });
  assert.equal(r.buttons[0].label, 'Shift');
});
```

- [ ] **Step 3: 跑測試確認失敗**

Run: `node --test tests/test_touchlayout.mjs`
Expected: FAIL（Cannot find module …/web/touchlayout.js）

- [ ] **Step 4: 寫 `web/touchlayout.js`**

```js
// 觸控佈局純邏輯：驗證/夾限 localStorage 佈局（不可信輸入）＋編輯盤面定義。
// 供 touchpad.js 與 node --test 共用。
// spec: docs/superpowers/specs/2026-07-10-player-touch-editor-design.md

// 內建鍵 id（dpad＝整組方向鍵；其餘為 apad 圓鈕）
export const BUILTIN_IDS = ['dpad', 'apad-escape', 'apad-enter', 'apad-ff3', 'apad-ff10'];

// 編輯盤面可加入的自訂鍵（決定/取消/»/»» 由內建鍵 chips 提供，不在此重複）
export const PALETTE = [
  { key: 'ShiftLeft', label: 'Shift' },
  ...Array.from({ length: 10 }, (_, n) => ({ key: 'Digit' + n, label: String(n) })),
];

const LABELS = new Map(PALETTE.map((p) => [p.key, p.label]));
const clamp = (n) => Math.min(95, Math.max(0, n));

// raw（JSON.parse 後任意值）→ {v:1,buttons:[…]} 或 null（壞資料＝當作沒紀錄）。
// 合法項：{id∈BUILTIN_IDS,x,y} 或 {key∈盤面,x,y}（label 一律以盤面為準）；
// x/y 夾限 0–95；重複 id/key 取第一個。
export function normalizeLayout(raw) {
  if (!raw || typeof raw !== 'object' || !Array.isArray(raw.buttons)) return null;
  const seen = new Set();
  const buttons = [];
  for (const b of raw.buttons) {
    if (!b || typeof b !== 'object') continue;
    const x = Number(b.x);
    const y = Number(b.y);
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
    if (typeof b.id === 'string' && BUILTIN_IDS.includes(b.id) && !seen.has(b.id)) {
      seen.add(b.id);
      buttons.push({ id: b.id, x: clamp(x), y: clamp(y) });
    } else if (typeof b.key === 'string' && LABELS.has(b.key) && !seen.has(b.key)) {
      seen.add(b.key);
      buttons.push({ key: b.key, label: LABELS.get(b.key), x: clamp(x), y: clamp(y) });
    }
  }
  return { v: 1, buttons };
}
```

- [ ] **Step 5: 跑測試確認通過**

Run: `node --test tests/test_touchlayout.mjs`
Expected: 9 pass, 0 fail

- [ ] **Step 6: Commit**

```powershell
git add web/touchlayout.js tests/test_touchlayout.mjs
git commit -m "feat(web): 觸控佈局純邏輯 touchlayout.js（normalizeLayout＋盤面）"
```

---

### Task 2: `touchpad.js` 佈局套用引擎＋建置注入

**Files:**
- Create: `web/touchpad.js`
- Modify: `pwa.py`（`_GATE_SNIPPET` 之後加常數；`write_game_pages` 的 `body_add` 行）
- Test: `tests/test_pwa_gamepages.py`

**Interfaces:**
- Consumes: Task 1 的 `normalizeLayout/PALETTE/BUILTIN_IDS`；頁面既有 `window.__WT.slug`、`#canvas`、`#apad`、`#apad-escape`。
- Produces（Task 3 依賴、同檔內）：
  - `load() → layout|null`、`save(layout)`、`clearSaved()`
  - `sendKey(type, code)`：對 canvas 派發
  - `makeCustom(btn) → el`（掛進 #apad、綁 touch 派發；`editing===true` 時不派發）
  - `applyLayout(layout|null)`：套用／復原全部
  - `customEls: Map<key, el>`、`positionEl(el,x,y)`、模組級 `let editing = false`

- [ ] **Step 1: 先改 pytest（TDD）**

`tests/test_pwa_gamepages.py` 新增：

```python
def test_write_game_pages_injects_touchpad(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    pwa.write_game_pages(dist, [{"label": "甲", "slug": "g", "cover_rel": None}])
    html = (dist / "play-g.html").read_text(encoding="utf-8")
    assert 'type="module" src="touchpad.js"' in html
```

Run: `python -m pytest tests/test_pwa_gamepages.py::test_write_game_pages_injects_touchpad -q`
Expected: FAIL

- [ ] **Step 2: `pwa.py` 加 snippet**

`_FF_STYLE` 定義之後加：

```python
# 玩家端觸控按鍵編輯器：套用/編輯 localStorage 佈局（入口鈕與樣式由 touchpad.js 動態建立）。
# 見 docs/superpowers/specs/2026-07-10-player-touch-editor-design.md
_TP_SNIPPET = '\n<script type="module" src="touchpad.js"></script>'
```

`write_game_pages` 內 `body_add = …` 行，在 `_FS_FALLBACK` 前插入 `_TP_SNIPPET`：

```python
        body_add = dl_snippet + save_snippet + wt_snippet + _CM_SNIPPET + _FAV_SNIPPET + _PT_SNIPPET + _CLOUD_SNIPPET + _TP_SNIPPET + _FS_FALLBACK + _POP_SNIPPET + install_snippet
```

Run: `python -m pytest tests/test_pwa_gamepages.py -q`
Expected: 18 passed

- [ ] **Step 3: 寫 `web/touchpad.js`（Task 2 版＝套用引擎）**

```js
// 玩家端觸控按鍵：套用 localStorage 佈局（內建鍵移位/隱藏、自訂鍵生成）。
// 編輯模式（拖拉/盤面）見「==== 編輯模式 ====」段；入口鈕僅觸控裝置顯示。
// spec: docs/superpowers/specs/2026-07-10-player-touch-editor-design.md
import { normalizeLayout, PALETTE, BUILTIN_IDS } from './touchlayout.js';

const SLUG = (window.__WT && window.__WT.slug) || '';
const KEY = 'ep-touch-' + SLUG;
const IS_TOUCH = window.matchMedia('(hover: none), (pointer: coarse)').matches;
const canvas = document.getElementById('canvas');
const apad = document.getElementById('apad');

// ---- 儲存 ----
function load() {
  try { return normalizeLayout(JSON.parse(localStorage.getItem(KEY))); } catch (e) { return null; }
}
function save(layout) {
  try { localStorage.setItem(KEY, JSON.stringify(layout)); } catch (e) { /* 私密瀏覽等，忽略 */ }
}
function clearSaved() { try { localStorage.removeItem(KEY); } catch (e) {} }

// ---- 派發按鍵：與 vendor simulateKeyboardEvent 同語意 ----
function sendKey(type, code) {
  const e = new Event(type, { bubbles: true });
  e.code = code;
  canvas.dispatchEvent(e);
}

// ---- 佈局套用 ----
let customEls = new Map(); // key → el
let editing = false;       // 編輯模式中自訂鍵不派發（編輯段落使用）

function positionEl(el, x, y) {
  el.style.position = 'fixed';
  el.style.left = x + '%';
  el.style.top = y + '%';
  el.style.right = 'auto';
  el.style.bottom = 'auto';
}
function resetEl(el) {
  el.style.position = '';
  el.style.left = '';
  el.style.top = '';
  el.style.right = '';
  el.style.bottom = '';
  el.style.display = '';
}

function makeCustom(btn) {
  const el = document.createElement('div');
  el.className = 'unselectable ep-tp-btn';
  el.dataset.tpKey = btn.key; // 不用 data-key：vendor 的綁定在頁面解析時已跑完
  el.textContent = btn.label;
  el.addEventListener('touchstart', (e) => {
    if (editing) return;
    e.preventDefault();
    el.classList.add('active');
    sendKey('keydown', btn.key);
  });
  const up = (e) => {
    if (editing) return;
    e.preventDefault();
    el.classList.remove('active');
    sendKey('keyup', btn.key);
  };
  el.addEventListener('touchend', up);
  el.addEventListener('touchcancel', up);
  // 插在 apad-escape 之前，保住 vendor :last-child 的 Enter 定位
  apad.insertBefore(el, document.getElementById('apad-escape'));
  return el;
}

// layout=null → 出廠預設；否則：清單未列的內建鍵隱藏、列了的移位、自訂鍵生成。
function applyLayout(layout) {
  for (const el of customEls.values()) el.remove();
  customEls = new Map();
  for (const id of BUILTIN_IDS) {
    const el = document.getElementById(id);
    if (el) resetEl(el);
  }
  if (!layout) return;
  const listed = new Set(layout.buttons.filter((b) => b.id).map((b) => b.id));
  for (const id of BUILTIN_IDS) {
    const el = document.getElementById(id);
    if (el && !listed.has(id)) el.style.display = 'none';
  }
  for (const b of layout.buttons) {
    if (b.id) {
      const el = document.getElementById(b.id);
      if (el) positionEl(el, b.x, b.y);
    } else {
      const el = makeCustom(b);
      positionEl(el, b.x, b.y);
      customEls.set(b.key, el);
    }
  }
}

// ---- 樣式：自訂鍵大小；圓形/半透明/按壓沿用 vendor #apad > * 規則 ----
const style = document.createElement('style');
style.textContent =
  '#apad > .ep-tp-btn{width:calc(.75*var(--controls-size));height:calc(.75*var(--controls-size));'
  + 'display:flex;align-items:center;justify-content:center;'
  + 'font-size:calc(.3*var(--controls-size));color:#000}';
document.head.append(style);

if (SLUG && canvas && apad) applyLayout(load());
```

- [ ] **Step 4: 語法與測試**

Run: `node --check web/touchpad.js; node --test tests/test_touchlayout.mjs; python -m pytest tests/ -q`
Expected: check 無輸出；node 9 pass；pytest 只剩已知 pre-existing 失敗

- [ ] **Step 5: 手動驗證套用引擎**

```powershell
python -c "import pwa; pwa.install_web_assets('dist')"
python "C:\Users\david\AppData\Local\Temp\claude\C--opensource-easyRPG-web\88fca23e-3098-45b3-a4a3-d08bee58270b\scratchpad\refresh_dist.py"
python -m http.server 8000 --directory dist
```

瀏覽器（DevTools 裝置模擬）開一款遊戲，console：

```js
localStorage.setItem('ep-touch-' + window.__WT.slug, JSON.stringify({ v: 1, buttons: [
  { id: 'dpad', x: 2, y: 55 },
  { key: 'Digit1', label: '1', x: 60, y: 85 },
  { key: 'ShiftLeft', label: 'Shift', x: 75, y: 85 },
] }));
location.reload();
```

Expected: 重整後只剩 dpad（移到左中）＋「1」＋「Shift」圓鈕；Esc/Enter/»/»» 消失；按「1」遊戲收到數字鍵（月藍２可驗）。清掉 `localStorage.removeItem(...)` 重整→回出廠。

- [ ] **Step 6: Commit**

```powershell
git add web/touchpad.js pwa.py tests/test_pwa_gamepages.py
git commit -m "feat(web): touchpad.js 佈局套用引擎＋遊戲頁注入"
```

---

### Task 3: 編輯模式（拖拉＋盤面＋垃圾桶＋入口鈕）

**Files:**
- Modify: `web/touchpad.js`（檔末 append 編輯段落；`applyLayout` 之後）

**Interfaces:**
- Consumes: Task 2 同檔的 `load/save/clearSaved/applyLayout/makeCustom/positionEl/customEls/editing/IS_TOUCH/PALETTE/BUILTIN_IDS`。
- Produces: 無對外（`#tp-edit` 入口鈕、`#tp-ui` 編輯 UI 皆自足）。

- [ ] **Step 1: 檔末 append 編輯模式**

在 `if (SLUG && canvas && apad) applyLayout(load());` **之前**插入以下整段，並把該行改為：

```js
if (SLUG && canvas && apad) {
  applyLayout(load());
  makeEntry();
}
```

插入段落：

```js
// ==== 編輯模式 ====
const TRASH_H = 72; // px：頂部移除區高度（拖放判定）

let work = null;     // 編輯中的佈局（直接改）
let snapshot = null; // 進入時的原始字串（取消用）
let ui = null;       // 編輯 UI 容器

const pct = (v, total) => Math.min(95, Math.max(0, (v / total) * 100));

function elFor(item) {
  return item.id ? document.getElementById(item.id) : customEls.get(item.key);
}

// 出廠狀態→以現時畫面位置建立可編輯佈局；已有紀錄→直接用
function currentAsLayout() {
  const saved = load();
  if (saved) return saved;
  const buttons = [];
  for (const id of BUILTIN_IDS) {
    const el = document.getElementById(id);
    if (!el) continue;
    const r = el.getBoundingClientRect();
    buttons.push({ id, x: pct(r.left, innerWidth), y: pct(r.top, innerHeight) });
  }
  return { v: 1, buttons };
}

function hookDrag(el, item) {
  if (!el || el.__tpDrag) { if (el) el.__tpItem = item; return; }
  el.__tpDrag = true;
  el.__tpItem = item;
  // capture：dpad 的觸點是內部 svg path，需在祖先捕獲期先攔下 vendor 的按鍵派發
  el.addEventListener('touchstart', (e) => {
    if (!editing) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    const cur = el.__tpItem;
    const t = e.touches[0];
    const r = el.getBoundingClientRect();
    const dx = t.clientX - r.left;
    const dy = t.clientY - r.top;
    const trashEl = document.getElementById('tp-trash');
    function onMove(ev) {
      ev.preventDefault();
      const m = ev.touches[0];
      cur.x = pct(m.clientX - dx, innerWidth);
      cur.y = pct(m.clientY - dy, innerHeight);
      positionEl(el, cur.x, cur.y);
      if (trashEl) trashEl.classList.toggle('hot', m.clientY < TRASH_H);
    }
    function onEnd(ev) {
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('touchend', onEnd);
      window.removeEventListener('touchcancel', onEnd);
      if (trashEl) trashEl.classList.remove('hot');
      const last = ev.changedTouches[0];
      if (last && last.clientY < TRASH_H) removeItem(cur);
    }
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('touchend', onEnd);
    window.addEventListener('touchcancel', onEnd);
  }, { capture: true });
}

function removeItem(item) {
  work.buttons = work.buttons.filter((b) => b !== item);
  const el = elFor(item);
  if (!el) return;
  if (item.id) el.style.display = 'none';
  else { el.remove(); customEls.delete(item.key); }
}

function addBuiltin(id) {
  if (work.buttons.some((b) => b.id === id)) return; // 已在畫面上＝無事
  const el = document.getElementById(id);
  if (!el) return;
  const item = { id, x: 45, y: 40 };
  work.buttons.push(item);
  el.style.display = '';
  positionEl(el, item.x, item.y);
  hookDrag(el, item);
}

function addKey(p, x, y) {
  if (work.buttons.some((b) => b.key === p.key)) return;
  const item = { key: p.key, label: p.label, x, y };
  work.buttons.push(item);
  const el = makeCustom(item);
  positionEl(el, x, y);
  customEls.set(p.key, el);
  hookDrag(el, item);
}

function mkBtn(label, fn) {
  const b = document.createElement('button');
  b.type = 'button';
  b.textContent = label;
  b.onclick = fn;
  return b;
}

function buildEditUi() {
  ui = document.createElement('div');
  ui.id = 'tp-ui';
  const top = document.createElement('div');
  top.id = 'tp-top';
  const trashEl = document.createElement('div');
  trashEl.id = 'tp-trash';
  trashEl.textContent = '🗑 拖到這裡移除';
  top.append(trashEl, mkBtn('完成', finishEdit), mkBtn('取消', cancelEdit), mkBtn('還原預設', resetDefault));
  const chips = document.createElement('div');
  chips.id = 'tp-chips';
  const builtins = [
    ['dpad', '方向鍵'], ['apad-enter', '決定'], ['apad-escape', '取消鍵'],
    ['apad-ff3', '»'], ['apad-ff10', '»»'],
  ];
  for (const [id, label] of builtins) chips.append(mkBtn(label, () => addBuiltin(id)));
  for (const p of PALETTE) chips.append(mkBtn(p.label, () => addKey(p, 45, 45)));
  chips.append(mkBtn('0–9 整排', () => {
    PALETTE.filter((p) => p.key.startsWith('Digit'))
      .forEach((p, i) => addKey(p, 2 + i * 9.5, 86));
  }));
  ui.append(top, chips);
  document.body.append(ui);
}

function startEdit() {
  if (editing) return;
  editing = true;
  try { snapshot = localStorage.getItem(KEY); } catch (e) { snapshot = null; }
  work = currentAsLayout();
  applyLayout(work);
  buildEditUi();
  document.body.classList.add('tp-editing');
  if (window.__epPause) window.__epPause(true, 'tp');
  for (const b of work.buttons) hookDrag(elFor(b), b);
}

function teardown() {
  document.body.classList.remove('tp-editing');
  if (ui) { ui.remove(); ui = null; }
  if (window.__epPause) window.__epPause(false, 'tp');
  editing = false;
}
function finishEdit() { save(work); teardown(); applyLayout(load()); }
function cancelEdit() {
  teardown();
  try {
    if (snapshot === null) localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, snapshot);
  } catch (e) {}
  applyLayout(load());
}
function resetDefault() { clearSaved(); teardown(); applyLayout(null); }

// 入口鈕：工具列（僅觸控裝置）
function makeEntry() {
  const bar = document.getElementById('saveui');
  if (!bar || !IS_TOUCH) return;
  const b = document.createElement('button');
  b.type = 'button';
  b.id = 'tp-edit';
  b.textContent = '按鍵';
  b.onclick = startEdit;
  bar.insertBefore(b, document.getElementById('dl-zip'));
}
```

- [ ] **Step 2: 編輯 UI 樣式**

Task 2 的 `style.textContent` 字串**追加**（同一個 style 元素）：

```js
  + '#tp-ui{position:fixed;inset:0;z-index:9000;background:rgba(6,9,28,.45)}'
  + '#tp-top{position:absolute;top:0;left:0;right:0;height:72px;display:flex;align-items:center;'
  + 'gap:8px;padding:6px 8px;box-sizing:border-box;background:rgba(6,9,28,.85)}'
  + '#tp-trash{flex:1;height:100%;border:2px dashed #888;border-radius:10px;color:#ccc;'
  + 'display:flex;align-items:center;justify-content:center;font-size:13px}'
  + '#tp-trash.hot{border-color:#f66;color:#f66}'
  + '#tp-ui button{padding:8px 12px;border-radius:8px;border:1px solid #2c3350;'
  + 'background:#171c2e;color:#c3c9ea;font-size:13px;flex:0 0 auto}'
  + '#tp-chips{position:absolute;bottom:0;left:0;right:0;display:flex;gap:8px;overflow-x:auto;'
  + 'padding:10px calc(10px + env(safe-area-inset-right)) calc(10px + env(safe-area-inset-bottom)) 10px;'
  + 'background:rgba(6,9,28,.85)}'
  + 'body.tp-editing #dpad,body.tp-editing #apad,body.tp-editing #apad>*{z-index:9001}';
```

- [ ] **Step 3: 語法與回歸**

Run: `node --check web/touchpad.js; node --test tests/test_touchlayout.mjs; python -m pytest tests/test_pwa_gamepages.py -q`
Expected: 全過

- [ ] **Step 4: 手動驗證編輯模式**

`python -c "import pwa; pwa.install_web_assets('dist')"` 後，DevTools 裝置模擬開遊戲頁：

1. 工具列出現「按鍵」鈕（桌機模式不出現）。
2. 點入：畫面變暗、遊戲暫停、頂部垃圾桶＋完成/取消/還原、底部 chips。
3. 點「0–9 整排」→ 十顆等距出現在下方；點 Shift → 出現在中央；全部可拖。
4. 把 »» 拖進頂部移除區 → 消失。
5. 完成 → 存檔；重整 → 佈局保留；再進編輯 → 取消 → 改動不留。
6. 還原預設 → 回出廠、localStorage 該鍵刪除。

- [ ] **Step 5: Commit**

```powershell
git add web/touchpad.js
git commit -m "feat(web): 觸控按鍵編輯模式（拖拉＋盤面＋垃圾桶＋入口鈕）"
```

---

### Task 4: dist 刷新＋手機 E2E＋收尾

**Files:** 無新程式碼。

- [ ] **Step 1: 刷新 dist**

```powershell
python "C:\Users\david\AppData\Local\Temp\claude\C--opensource-easyRPG-web\88fca23e-3098-45b3-a4a3-d08bee58270b\scratchpad\refresh_dist.py"
```

Expected: 27 頁重生成；`touchpad.js`/`touchlayout.js` 進 dist。

- [ ] **Step 2: E2E checklist（DevTools 裝置模擬或手機，月藍傳奇２）**

1. 「按鍵」入口只在觸控環境出現。
2. 加 0–9 整排＋Shift → 拖位 → 完成 → 重整保留。
3. 遊戲內按鍵輸入事件吃得到 0–9／Shift。
4. 移除 dpad 再用 chips 加回。
5. 還原預設後與出廠完全一致（含 »/»» 位置）。
6. 桌機（非觸控）：無入口鈕、頁面無異狀。

- [ ] **Step 3: 收尾**

跑 `python -m pytest tests/ -q`＋`node --test tests/test_touchlayout.mjs tests/test_savemerge.mjs`，全過（除已知 pre-existing）後走 superpowers:finishing-a-development-branch（合併回 main）。E2E 結果記入本檔末尾。

---

## E2E 結果

（執行後填寫）
