// 雲端存檔：把雲端 UI 填進「存檔」面板的 #sp-cloud。用 _SAVE_UI 暴露的 window.__epSaves 與地基 account.js。
import {
  doc, getDoc, getDocs, setDoc, deleteDoc, collection, serverTimestamp, Bytes,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser,
} from './account.js';

const SLUG = (window.__WT && window.__WT.slug) || '';
const box = document.getElementById('sp-cloud');
const MAXBYTES = 900 * 1024;

if (box) build();

function build() {
  const status = document.createElement('div');
  status.className = 'sp-status'; status.textContent = '雲端存檔';
  const auth = document.createElement('div');
  auth.className = 'sp-status';
  const up = document.createElement('button');
  up.type = 'button'; up.className = 'sp-btn'; up.textContent = '上傳到雲端';
  const down = document.createElement('button');
  down.type = 'button'; down.className = 'sp-btn'; down.textContent = '從雲端取回';
  box.append(status, auth, up, down);

  if (!isReady()) {
    status.textContent = '雲端功能需站長設定後端';
    up.disabled = true; down.disabled = true;
    return;
  }

  function renderAuth(u) {
    auth.innerHTML = '';
    if (u) {
      auth.append(document.createTextNode((u.displayName || '已登入') + ' '));
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'sp-link'; b.textContent = '登出';
      b.onclick = () => signOutUser();
      auth.append(b);
      loadStatus(u.uid);
    } else {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'sp-link'; b.textContent = '用 Google 登入';
      b.onclick = () => signInWithGoogle().catch(() => alert('登入失敗'));
      auth.append(b);
      status.textContent = '登入後可用雲端存檔';
    }
  }
  onAuthChange(renderAuth);

  async function loadStatus(uid) {
    try {
      const snap = await getDoc(doc(db, 'users', uid, 'saves', SLUG));
      const t = snap.exists() && snap.data().updatedAt && snap.data().updatedAt.toDate
        ? snap.data().updatedAt.toDate().toLocaleString() : null;
      status.textContent = t ? ('上次雲端備份：' + t) : '尚未備份';
    } catch (e) { status.textContent = '雲端狀態載入失敗'; }
  }

  up.onclick = async () => {
    const u = currentUser();
    if (!u) { signInWithGoogle().catch(() => alert('登入失敗')); return; }
    const files = window.__epSaves ? window.__epSaves.read() : [];
    if (!files.length) { alert('找不到本機存檔（請先在遊戲裡存檔）'); return; }
    if (!confirm('上傳會用本機存檔覆蓋雲端，確定？')) return;
    up.disabled = true;
    try {
      const names = [];
      for (const f of files) {
        if (f.data.length > MAXBYTES) { alert('略過過大的存檔：' + f.name); continue; }
        await setDoc(doc(db, 'users', u.uid, 'saves', SLUG, 'files', f.name),
          { data: Bytes.fromUint8Array(f.data), updatedAt: serverTimestamp() });
        names.push(f.name);
      }
      const snap = await getDocs(collection(db, 'users', u.uid, 'saves', SLUG, 'files'));
      for (const d of snap.docs) { if (!names.includes(d.id)) await deleteDoc(d.ref); }
      await setDoc(doc(db, 'users', u.uid, 'saves', SLUG),
        { updatedAt: serverTimestamp(), names });
      alert('已上傳 ' + names.length + ' 個存檔到雲端');
      loadStatus(u.uid);
    } catch (e) { alert('上傳失敗，請稍後再試'); }
    up.disabled = false;
  };

  down.onclick = async () => {
    const u = currentUser();
    if (!u) { signInWithGoogle().catch(() => alert('登入失敗')); return; }
    if (!confirm('取回會用雲端存檔覆蓋本機，確定？')) return;
    down.disabled = true;
    try {
      const parent = await getDoc(doc(db, 'users', u.uid, 'saves', SLUG));
      const names = (parent.exists() && parent.data().names) || [];
      if (!names.length) { alert('雲端沒有存檔'); down.disabled = false; return; }
      const files = [];
      for (const name of names) {
        const fsnap = await getDoc(doc(db, 'users', u.uid, 'saves', SLUG, 'files', name));
        if (fsnap.exists() && fsnap.data().data) {
          files.push({ name, data: fsnap.data().data.toUint8Array() });
        }
      }
      if (!files.length) { alert('雲端沒有存檔'); down.disabled = false; return; }
      await window.__epSaves.write(files);
      alert('已從雲端取回 ' + files.length + ' 個存檔，將重新載入遊戲。');
      location.reload();
    } catch (e) { alert('取回失敗，請稍後再試'); down.disabled = false; }
  };
}
