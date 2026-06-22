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
