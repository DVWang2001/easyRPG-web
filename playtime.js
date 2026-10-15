// 遊玩時間：離線也照記。計時＋localStorage 緩衝完全零依賴；雲端同步才動態載入 firebase。
// 注意：這支不可以有頂層 import——離線時 gstatic 抓不到會讓整個模組不執行，一秒都記不到。
const SLUG = (window.__WT && window.__WT.slug) || '';
const label = document.getElementById('pt-label');
const BUF_KEY = 'ep-pt-' + SLUG;
const CLOUD_KEY = 'ep-ptc-' + SLUG;

// 雲端已存的總秒數；離線開頁時先用上次讀到的快取值，不然畫面會從 0 開始像資料掉了
// ponytail: 快取只依 slug 不依 uid，換帳號登入前會短暫顯示上一位的總時數；登出即清除
let cloudSeconds = parseInt(localStorage.getItem(CLOUD_KEY) || '0', 10) || 0;
let live = 0;         // 本次開頁、尚未併入 localStorage 緩衝的記憶體秒數
let flushing = false;
let watching = false; // 是否已掛上 onAuthChange
let fbP = null;       // firebase + account.js 的動態載入

function buffer() { return parseInt(localStorage.getItem(BUF_KEY) || '0', 10) || 0; }
function setBuffer(n) {
  if (n > 0) localStorage.setItem(BUF_KEY, String(n));
  else localStorage.removeItem(BUF_KEY);
}
function setCloud(n) {
  cloudSeconds = n;
  if (n > 0) localStorage.setItem(CLOUD_KEY, String(n));
  else localStorage.removeItem(CLOUD_KEY);
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

// 動態載入雲端相依；失敗（離線）就把 promise 丟掉，下次上線再試
function fb() {
  if (!fbP) {
    fbP = Promise.all([
      import('https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js'),
      import('./account.js'),
    ]).catch((e) => { fbP = null; throw e; });
  }
  return fbP;
}

if (SLUG) start();

function start() {
  render();
  // 每秒累加（僅可見時）；每累積 5 秒併入 localStorage 緩衝（本機持久，不碰 DB）
  setInterval(() => {
    if (document.visibilityState === 'visible') { live += 1; render(); }
    if (live >= 5) { setBuffer(buffer() + live); live = 0; }
  }, 1000);

  watchAuth();

  // 離開頁面：併入緩衝後寫一次
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') flush();
  });
  window.addEventListener('pagehide', flush);
  // 一連上網就補寫，不必等玩家關分頁
  window.addEventListener('online', () => { watchAuth(); flush(); });
}

// 登入後讀一次雲端總時數；登出歸零
async function watchAuth() {
  if (watching) return;
  try {
    const [, acc] = await fb();
    if (!acc.isReady()) return;
    acc.onAuthChange((u) => {
      if (u) loadCloud(u.uid);
      else { setCloud(0); render(); }
    });
    watching = true;
  } catch (e) { /* 離線：純本機模式，上線後再掛 */ }
}

async function loadCloud(uid) {
  try {
    const [fs, acc] = await fb();
    const snap = await fs.getDoc(fs.doc(acc.db, 'users', uid, 'history', SLUG));
    setCloud((snap.exists() && typeof snap.data().totalSeconds === 'number')
      ? snap.data().totalSeconds : 0);
  } catch (e) { /* 讀不到就沿用快取值 */ }
  render();
  flush(); // 補寫離線期間累積的緩衝
}

async function flush() {
  if (live > 0) { setBuffer(buffer() + live); live = 0; }
  const amount = buffer();
  // 離線時別碰 Firestore：它的離線佇列上線後會自己補送，跟本機緩衝重送會湊成雙倍
  if (amount <= 0 || flushing || !navigator.onLine) return;
  flushing = true;
  try {
    const [fs, acc] = await fb();
    const u = acc.isReady() ? acc.currentUser() : null;
    if (u) {
      await fs.setDoc(
        fs.doc(acc.db, 'users', u.uid, 'history', SLUG),
        { totalSeconds: fs.increment(amount), lastPlayedAt: fs.serverTimestamp() },
        { merge: true },
      );
      setCloud(cloudSeconds + amount);
      setBuffer(buffer() - amount); // 只扣已寫量，期間新增的留著
      render();
    }
  } catch (e) { /* 失敗：緩衝留著，下次離開或上線再補寫 */ }
  flushing = false;
}
