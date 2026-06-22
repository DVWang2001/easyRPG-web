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
