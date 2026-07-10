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
