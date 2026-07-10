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
  + 'font-size:calc(.3*var(--controls-size));color:#000}'
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
document.head.append(style);

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

if (SLUG && canvas && apad) {
  applyLayout(load());
  makeEntry();
}
