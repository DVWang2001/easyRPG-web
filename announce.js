// 站務公告：首頁橫幅（#announce）或公告頁歷史列表（#announce-list）。
import {
  collection, addDoc, getDocs, query, orderBy, limit,
  serverTimestamp,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, isAdmin,
} from './account.js';

const col = () => collection(db, 'announcements');

function dateStr(ts) {
  return (ts && ts.toDate) ? ts.toDate().toLocaleDateString() : '';
}

// ---- Quill lazy loader ----
let _quill = null, _qp = null;
function ensureQuill() {
  if (window.Quill) return Promise.resolve();
  if (_qp) return _qp;
  _qp = new Promise((ok, no) => {
    const c = document.createElement('link');
    c.rel = 'stylesheet'; c.href = 'https://cdn.quilljs.com/1.3.7/quill.snow.css';
    document.head.appendChild(c);
    const s = document.createElement('script');
    s.src = 'https://cdn.quilljs.com/1.3.7/quill.min.js';
    s.onload = ok; s.onerror = () => no(new Error('Quill 載入失敗'));
    document.head.appendChild(s);
  });
  return _qp;
}

// ======== BANNER MODE (homepage #announce) ========
function initBanner() {
  const host = document.getElementById('announce');
  let latest = null, admin = false;

  const banner = document.createElement('div');
  banner.className = 'ann-banner';
  const tools = document.createElement('div');
  tools.className = 'ann-tools';
  const closeBtn = document.createElement('button');
  closeBtn.type = 'button'; closeBtn.className = 'ann-close';
  closeBtn.textContent = '✕'; closeBtn.title = '關閉';
  tools.append(closeBtn);
  const body = document.createElement('div');
  body.className = 'ann-body';
  const meta = document.createElement('div');
  meta.className = 'ann-meta';
  const more = document.createElement('a');
  more.href = 'announce.html'; more.className = 'ann-more';
  more.textContent = '查看所有公告 →';
  banner.append(tools, body, meta, more);
  host.appendChild(banner);

  function ver() {
    return (latest && latest.updatedAt && latest.updatedAt.toMillis)
      ? String(latest.updatedAt.toMillis()) : '';
  }

  function render() {
    const html = (latest && latest.html) ? latest.html : '';
    if (!html) {
      if (admin) {
        body.innerHTML = '<em class="ann-empty">（目前沒有公告）</em>';
        meta.textContent = ''; closeBtn.hidden = true;
        host.hidden = false;
      } else { host.hidden = true; }
      return;
    }
    let dismissed = '';
    try { dismissed = localStorage.getItem('ann-dismissed') || ''; } catch (e) {}
    if (!admin && ver() && dismissed === ver()) { host.hidden = true; return; }

    body.innerHTML = DOMPurify.sanitize(html, { ALLOWED_URI_REGEXP: /^(?:https?|mailto):/i });
    const c = dateStr(latest.createdAt), u = dateStr(latest.updatedAt);
    meta.textContent = c ? ('發布於 ' + c + (u && u !== c ? ' · 編輯於 ' + u : '')) : '';
    closeBtn.hidden = false; host.hidden = false;
  }

  closeBtn.onclick = () => {
    if (ver()) try { localStorage.setItem('ann-dismissed', ver()); } catch (e) {}
    host.hidden = true;
  };

  (async () => {
    try {
      const snap = await getDocs(query(col(), orderBy('createdAt', 'desc'), limit(1)));
      latest = snap.empty ? null : snap.docs[0].data();
    } catch (e) { latest = null; }
    render();
  })();

  onAuthChange(u => { admin = !!(u && isAdmin(u.uid)); render(); });
}

// ======== LIST MODE (announce.html #announce-list) ========
function initList() {
  const host = document.getElementById('announce-list');
  let admin = false, items = [];

  // Admin: new-announcement section
  const sec = document.createElement('div');
  sec.className = 'ann-new'; sec.hidden = true;
  const newBtn = document.createElement('button');
  newBtn.type = 'button'; newBtn.className = 'ann-newbtn';
  newBtn.textContent = '＋ 發布新公告';
  const edWrap = document.createElement('div');
  edWrap.className = 'ann-editor'; edWrap.hidden = true;
  const qEl = document.createElement('div'); qEl.className = 'ann-quill';
  const bar = document.createElement('div'); bar.className = 'ann-editbar';
  const subBtn = document.createElement('button');
  subBtn.type = 'button'; subBtn.textContent = '發布';
  const canBtn = document.createElement('button');
  canBtn.type = 'button'; canBtn.className = 'ann-cancel'; canBtn.textContent = '取消';
  bar.append(subBtn, canBtn);
  edWrap.append(qEl, bar);
  sec.append(newBtn, edWrap);
  host.before(sec);

  const empty = document.createElement('p');
  empty.className = 'ann-list-empty'; empty.textContent = '還沒有公告。';
  host.appendChild(empty);

  newBtn.onclick = async () => {
    try { await ensureQuill(); } catch (e) { alert('編輯器載入失敗'); return; }
    if (!_quill) {
      _quill = new Quill(qEl, {
        theme: 'snow',
        modules: { toolbar: [
          [{ header: [1, 2, 3, false] }], ['bold', 'italic'],
          [{ list: 'ordered' }, { list: 'bullet' }], ['link'],
        ] },
      });
    }
    _quill.setText('');
    newBtn.hidden = true; edWrap.hidden = false;
  };

  canBtn.onclick = () => { edWrap.hidden = true; newBtn.hidden = false; };

  subBtn.onclick = async () => {
    const u = currentUser();
    if (!u || !isAdmin(u.uid)) { alert('沒有權限'); return; }
    const text = _quill.getText().trim();
    if (!text) { alert('請輸入內容'); return; }
    const html = _quill.root.innerHTML;
    if (new Blob([html]).size > 50000) { alert('內文過長，請精簡'); return; }
    try {
      await addDoc(col(), { html, createdAt: serverTimestamp(), updatedAt: serverTimestamp() });
    } catch (e) { alert('發布失敗，請稍後再試'); return; }
    edWrap.hidden = true; newBtn.hidden = false;
    await load();
  };

  function renderList() {
    host.querySelectorAll('.ann-item').forEach(el => el.remove());
    empty.hidden = items.length > 0;
    sec.hidden = !admin;
    items.forEach(d => {
      const card = document.createElement('article');
      card.className = 'ann-item ann-banner';
      const b = document.createElement('div'); b.className = 'ann-body';
      b.innerHTML = DOMPurify.sanitize(d.html || '', { ALLOWED_URI_REGEXP: /^(?:https?|mailto):/i });
      const m = document.createElement('div'); m.className = 'ann-meta';
      const c = dateStr(d.createdAt), u = dateStr(d.updatedAt);
      m.textContent = c ? ('發布於 ' + c + (u && u !== c ? ' · 編輯於 ' + u : '')) : '';
      card.append(b, m);
      host.appendChild(card);
    });
  }

  async function load() {
    try {
      const snap = await getDocs(query(col(), orderBy('createdAt', 'desc')));
      items = [];
      snap.forEach(d => { const x = d.data(); if (x.html) items.push(x); });
    } catch (e) { items = []; }
    renderList();
  }

  onAuthChange(u => { admin = !!(u && isAdmin(u.uid)); renderList(); });
  load();
}

// ---- Boot ----
if (isReady()) {
  if (document.getElementById('announce-list')) initList();
  else if (document.getElementById('announce')) initBanner();
}
