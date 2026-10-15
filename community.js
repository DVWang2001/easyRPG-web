// 留言＋五星評分面板。依賴頁面注入的 window.__WT（slug/title）與地基 account.js。
import {
  collection, addDoc, getDocs, deleteDoc, doc, setDoc, query, orderBy, serverTimestamp,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser, isAdmin,
} from './account.js';

const GM = window.__WT || { slug: '', title: '' };
let myStars = 0; // 目前使用者的評分（0＝未評）

// ---- 浮層 DOM ----
const panel = document.createElement('div');
panel.id = 'cm-panel';
panel.hidden = true;
panel.innerHTML = `
  <div class="cm-backdrop"></div>
  <div class="cm-dialog">
    <div class="cm-head">
      <strong class="cm-gametitle"></strong>
      <span class="cm-auth"></span>
      <button class="cm-close" type="button">✕</button>
    </div>
    <div class="cm-rating">
      <span class="cm-avg"></span>
      <span class="cm-stars" role="group" aria-label="你的評分"></span>
    </div>
    <div class="cm-list"></div>
    <div class="cm-compose">
      <textarea class="cm-text" maxlength="500" placeholder="留個言…（最多 500 字）"></textarea>
      <button class="cm-submit" type="button">送出</button>
    </div>
  </div>`;
document.body.appendChild(panel);
panel.querySelector('.cm-gametitle').textContent = GM.title || '留言';

const listEl = panel.querySelector('.cm-list');
const authEl = panel.querySelector('.cm-auth');
const avgEl = panel.querySelector('.cm-avg');
const starsEl = panel.querySelector('.cm-stars');
const textEl = panel.querySelector('.cm-text');

function openPanel() {
  panel.hidden = false;
  if (window.__epPause) window.__epPause(true, 'cm');
  loadRatings();
  loadList();
}
function closePanel() {
  panel.hidden = true;
  if (window.__epPause) window.__epPause(false, 'cm');
}

const openBtn = document.getElementById('cm-open');
if (openBtn) openBtn.onclick = () => {
  if (!isReady()) { alert('站長尚未設定後端，留言功能暫不可用'); return; }
  openPanel();
};
panel.querySelector('.cm-close').onclick = closePanel;
panel.querySelector('.cm-backdrop').onclick = closePanel;

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
  renderStars(); // 登入狀態變了，星星可點性也變
}

// ---- 評分 ----
async function loadRatings() {
  avgEl.textContent = '評分載入中…';
  try {
    const snap = await getDocs(collection(db, 'games', GM.slug, 'ratings'));
    let sum = 0; let n = 0; myStars = 0;
    const u = currentUser();
    snap.forEach((d) => {
      const s = d.data().stars;
      if (typeof s === 'number') { sum += s; n += 1; }
      if (u && d.id === u.uid) myStars = s || 0;
    });
    avgEl.textContent = n ? ('★ ' + (sum / n).toFixed(1) + ' · ' + n + ' 人') : '尚無評分';
    renderStars();
  } catch (e) {
    avgEl.textContent = '評分載入失敗';
  }
}
function renderStars() {
  starsEl.innerHTML = '';
  const u = currentUser();
  for (let k = 1; k <= 5; k += 1) {
    const star = document.createElement('button');
    star.type = 'button';
    star.className = 'cm-star' + (k <= myStars ? ' on' : '');
    star.textContent = '★';
    star.disabled = !u;
    star.title = u ? (k + ' 星') : '登入後可評分';
    star.onclick = () => rate(k);
    starsEl.appendChild(star);
  }
}
async function rate(k) {
  const u = currentUser();
  if (!u) { signInWithGoogle().catch(() => alert('登入失敗')); return; }
  try {
    if (k === myStars) { // 再點同一顆已選的星 → 收回評分
      await deleteDoc(doc(db, 'games', GM.slug, 'ratings', u.uid));
    } else {
      await setDoc(doc(db, 'games', GM.slug, 'ratings', u.uid), {
        stars: k, authorUid: u.uid, updatedAt: serverTimestamp(),
      });
    }
    loadRatings();
  } catch (e) { alert('評分失敗，請稍後再試'); }
}

// ---- 留言清單（一次性查詢）----
async function loadList() {
  listEl.textContent = '載入中…';
  try {
    const q = query(
      collection(db, 'games', GM.slug, 'comments'),
      orderBy('createdAt', 'desc'),
    );
    const snap = await getDocs(q);
    listEl.innerHTML = '';
    if (snap.empty) {
      listEl.innerHTML = '<p class="cm-empty">還沒有留言，搶頭香！</p>';
      return;
    }
    snap.forEach((d) => listEl.appendChild(renderItem(d.id, d.data())));
  } catch (e) {
    listEl.textContent = '載入失敗，請稍後再試';
  }
}
function renderItem(id, data) {
  const item = document.createElement('div');
  item.className = 'cm-item';
  const meta = document.createElement('div');
  meta.className = 'cm-meta';
  const date = (data.createdAt && data.createdAt.toDate)
    ? data.createdAt.toDate().toLocaleString() : '';
  meta.textContent = (data.authorName || '匿名') + ' · ' + date;
  item.appendChild(meta);
  const body = document.createElement('div');
  body.className = 'cm-text-body';
  body.textContent = data.text || ''; // 純文字，textContent → 無 XSS
  item.appendChild(body);

  const u = currentUser();
  if (u && (u.uid === data.authorUid || isAdmin(u.uid))) {
    const del = document.createElement('button');
    del.type = 'button'; del.className = 'cm-del'; del.textContent = '刪除';
    del.onclick = async () => {
      if (!confirm('確定刪除這則留言？')) return;
      try {
        await deleteDoc(doc(db, 'games', GM.slug, 'comments', id));
        loadList();
      } catch (e) { alert('刪除失敗'); }
    };
    item.appendChild(del);
  }
  return item;
}

// ---- 送出留言 ----
panel.querySelector('.cm-submit').onclick = async () => {
  const u = currentUser();
  if (!u) { signInWithGoogle().catch(() => alert('登入失敗')); return; }
  const text = textEl.value.trim();
  if (!text) { alert('請輸入留言'); return; }
  if (text.length > 500) { alert('留言過長（上限 500 字）'); return; }
  try {
    await addDoc(collection(db, 'games', GM.slug, 'comments'), {
      text,
      authorName: u.displayName || '匿名',
      authorUid: u.uid,
      createdAt: serverTimestamp(),
    });
    textEl.value = '';
    loadList();
  } catch (e) { alert('送出失敗，請稍後再試'); }
};
