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
