// 遊玩時間：在遊戲頁累計「分頁可見」的秒數，離開頁面才寫一次 Firestore（增量）。私有，依賴 account.js。
import {
  doc, getDoc, setDoc, serverTimestamp, increment,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import { db, isReady, currentUser, onAuthChange } from './account.js';

const SLUG = (window.__WT && window.__WT.slug) || '';
const label = document.getElementById('pt-label');
const BUF_KEY = 'ep-pt-' + SLUG;

let cloudSeconds = 0; // 雲端已存的總秒數（登入後讀一次）
let live = 0;         // 本次開頁、尚未併入 localStorage 緩衝的記憶體秒數
let flushing = false;

function buffer() { return parseInt(localStorage.getItem(BUF_KEY) || '0', 10) || 0; }
function setBuffer(n) {
  if (n > 0) localStorage.setItem(BUF_KEY, String(n));
  else localStorage.removeItem(BUF_KEY);
}
function fmt(s) {
  s = Math.floor(s);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h) return '已遊玩 ' + h + 'h' + (m ? ' ' + m + 'm' : '');
  if (m) return '已遊玩 ' + m + 'm';
  return '已遊玩 ' + s + 's';
}
function render() {
  if (label) label.textContent = fmt(cloudSeconds + buffer() + live);
}

if (SLUG) start();

function start() {
  render();
  // 每秒累加（僅可見時）；每累積 5 秒併入 localStorage 緩衝（本機持久，不碰 DB）
  setInterval(() => {
    if (document.visibilityState === 'visible') { live += 1; render(); }
    if (live >= 5) { setBuffer(buffer() + live); live = 0; }
  }, 1000);

  // 登入後讀一次雲端總時數；登出歸零
  if (isReady()) {
    onAuthChange((u) => {
      if (u) loadCloud(u.uid);
      else { cloudSeconds = 0; render(); }
    });
  }

  // 離開頁面：併入緩衝後寫一次
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') flush();
  });
  window.addEventListener('pagehide', flush);
}

async function loadCloud(uid) {
  try {
    const snap = await getDoc(doc(db, 'users', uid, 'history', SLUG));
    cloudSeconds = (snap.exists() && typeof snap.data().totalSeconds === 'number')
      ? snap.data().totalSeconds : 0;
  } catch (e) { cloudSeconds = 0; }
  render();
}

async function flush() {
  if (live > 0) { setBuffer(buffer() + live); live = 0; }
  const u = isReady() ? currentUser() : null;
  const amount = buffer();
  if (!u || amount <= 0 || flushing) return;
  flushing = true;
  try {
    await setDoc(
      doc(db, 'users', u.uid, 'history', SLUG),
      { totalSeconds: increment(amount), lastPlayedAt: serverTimestamp() },
      { merge: true },
    );
    cloudSeconds += amount;
    setBuffer(buffer() - amount); // 只扣已寫量，期間新增的留著
  } catch (e) { /* 失敗：緩衝留著，下次離開再補寫 */ }
  flushing = false;
}
