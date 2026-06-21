// 攻略面板：讀/投稿/刪除某遊戲的攻略。依賴頁面注入的 window.__WT 與全域 Quill/DOMPurify。
import {
  collection, addDoc, getDocs, deleteDoc, doc, query, orderBy, serverTimestamp,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser, isAdmin,
} from './account.js';
import { imageUpload } from './firebase-config.js';

const WT = window.__WT || { slug: '', title: '' };
let quill = null;

// ---- 浮層 DOM ----
const panel = document.createElement('div');
panel.id = 'wt-panel';
panel.hidden = true;
panel.innerHTML = `
  <div class="wt-backdrop"></div>
  <div class="wt-dialog">
    <div class="wt-head">
      <strong class="wt-gametitle"></strong>
      <span class="wt-auth"></span>
      <button class="wt-close" type="button">✕</button>
    </div>
    <div class="wt-list"></div>
    <div class="wt-compose">
      <button class="wt-new" type="button">＋ 投稿攻略</button>
      <div class="wt-editor" hidden>
        <input class="wt-title" type="text" maxlength="200" placeholder="攻略標題…">
        <div class="wt-quill"></div>
        <div class="wt-editor-bar">
          <button class="wt-submit" type="button">送出</button>
          <button class="wt-cancel" type="button">取消</button>
        </div>
      </div>
    </div>
  </div>`;
document.body.appendChild(panel);
panel.querySelector('.wt-gametitle').textContent = WT.title || '攻略';

const listEl = panel.querySelector('.wt-list');
const authEl = panel.querySelector('.wt-auth');
const editorEl = panel.querySelector('.wt-editor');
const quillEl = panel.querySelector('.wt-quill');
const titleEl = panel.querySelector('.wt-title');

function openPanel() { panel.hidden = false; loadList(); }
function closePanel() { panel.hidden = true; }

const openBtn = document.getElementById('wt-open');
if (openBtn) openBtn.onclick = () => {
  if (!isReady()) { alert('站長尚未設定後端，攻略功能暫不可用'); return; }
  openPanel();
};
panel.querySelector('.wt-close').onclick = closePanel;
panel.querySelector('.wt-backdrop').onclick = closePanel;

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
}

// ---- 攻略清單（一次性查詢）----
async function loadList() {
  listEl.textContent = '載入中…';
  try {
    const q = query(
      collection(db, 'games', WT.slug, 'walkthroughs'),
      orderBy('createdAt', 'desc'),
    );
    const snap = await getDocs(q);
    listEl.innerHTML = '';
    if (snap.empty) {
      listEl.innerHTML = '<p class="wt-empty">還沒有攻略，來當第一個投稿的人！</p>';
      return;
    }
    snap.forEach((d) => listEl.appendChild(renderItem(d.id, d.data())));
  } catch (e) {
    listEl.textContent = '載入失敗，請稍後再試';
  }
}

function renderItem(id, data) {
  const item = document.createElement('details');
  item.className = 'wt-item';
  const sum = document.createElement('summary');
  const date = (data.createdAt && data.createdAt.toDate)
    ? data.createdAt.toDate().toLocaleDateString() : '';
  sum.textContent = (data.title || '(無標題)') + ' — '
    + (data.authorName || '匿名') + ' ' + date;
  item.appendChild(sum);

  const body = document.createElement('div');
  body.className = 'wt-body';
  body.innerHTML = DOMPurify.sanitize(data.html || '', {
    ALLOWED_URI_REGEXP: /^(?:https?|mailto):/i,
  });  // 公開內容必經消毒；連結/圖片來源限 http(s)/mailto
  item.appendChild(body);

  const u = currentUser();
  if (u && (u.uid === data.authorUid || isAdmin(u.uid))) {
    const del = document.createElement('button');
    del.type = 'button'; del.className = 'wt-del'; del.textContent = '刪除';
    del.onclick = async () => {
      if (!confirm('確定刪除這篇攻略？')) return;
      try {
        await deleteDoc(doc(db, 'games', WT.slug, 'walkthroughs', id));
        loadList();
      } catch (e) { alert('刪除失敗'); }
    };
    item.appendChild(del);
  }
  return item;
}

// ---- 圖片自動上傳（不走 base64）----
async function uploadImage(file) {
  if (imageUpload.provider === 'imgbb') {
    const form = new FormData();
    form.append('image', file);
    const res = await fetch(
      'https://api.imgbb.com/1/upload?key=' + encodeURIComponent(imageUpload.apiKey),
      { method: 'POST', body: form });
    if (!res.ok) throw new Error('imgbb ' + res.status);
    const j = await res.json();
    if (!j || !j.success || !j.data || !j.data.url) throw new Error('imgbb upload failed');
    return j.data.url;
  }
  throw new Error('未設定圖床');
}

function imageHandler() {
  const input = document.createElement('input');
  input.type = 'file'; input.accept = 'image/*';
  input.onchange = async () => {
    const file = input.files[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) { alert('圖片過大（上限 5MB）'); return; }
    const range = quill.getSelection(true) || { index: quill.getLength() };
    const ph = '（圖片上傳中…）';
    quill.insertText(range.index, ph);
    try {
      const url = await uploadImage(file);
      quill.deleteText(range.index, ph.length);
      quill.insertEmbed(range.index, 'image', url);
      quill.setSelection(range.index + 1);
    } catch (e) {
      quill.deleteText(range.index, ph.length);
      alert('圖片上傳失敗，可改貼網址或稍後再試');
    }
  };
  input.click();
}

// ---- 投稿編輯器 ----
function openEditor() {
  editorEl.hidden = false;
  if (!quill) {
    quill = new Quill(quillEl, {
      theme: 'snow',
      modules: {
        toolbar: {
          container: [
            [{ header: [1, 2, 3, false] }],
            ['bold', 'italic'],
            [{ list: 'ordered' }, { list: 'bullet' }],
            ['link', 'image'],
          ],
          handlers: { image: imageHandler },
        },
      },
    });
  }
}
panel.querySelector('.wt-new').onclick = () => {
  if (!currentUser()) { signInWithGoogle().then(openEditor).catch(() => alert('登入失敗')); return; }
  openEditor();
};
panel.querySelector('.wt-cancel').onclick = () => {
  titleEl.value = '';
  if (quill) quill.setText('');
  editorEl.hidden = true;
};
panel.querySelector('.wt-submit').onclick = async () => {
  const u = currentUser();
  if (!u) { alert('請先登入'); return; }
  const title = titleEl.value.trim();
  const html = quill ? quill.root.innerHTML : '';
  if (!title) { alert('請輸入標題'); return; }
  if (title.length > 200) { alert('標題過長（上限 200 字）'); return; }
  if (new Blob([html]).size > 50000) { alert('內文過長（請精簡或減少圖片數量）'); return; }
  try {
    await addDoc(collection(db, 'games', WT.slug, 'walkthroughs'), {
      title, html,
      authorName: u.displayName || '匿名',
      authorUid: u.uid,
      createdAt: serverTimestamp(),
    });
    titleEl.value = '';
    if (quill) quill.setText('');
    editorEl.hidden = true;
    loadList();
  } catch (e) { alert('投稿失敗，請稍後再試'); }
};
