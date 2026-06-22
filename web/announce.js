// 站務公告：首頁頂部橫幅（單則，可關閉）；管理員可內嵌富文字編輯。依賴地基 account.js。
import {
  doc, getDoc, setDoc, serverTimestamp,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, isAdmin,
} from './account.js';

const host = document.getElementById('announce');
if (host && isReady()) init();

function init() {
  let data = null;        // { html, createdAt, updatedAt } 或 null
  let isAdminNow = false;
  let quill = null;
  let quillLoading = null;

  // ---- 橫幅 DOM ----
  const banner = document.createElement('div');
  banner.className = 'ann-banner';
  const tools = document.createElement('div');
  tools.className = 'ann-tools';
  const editBtn = document.createElement('button');
  editBtn.type = 'button'; editBtn.className = 'ann-edit'; editBtn.textContent = '✎ 編輯'; editBtn.hidden = true;
  const closeBtn = document.createElement('button');
  closeBtn.type = 'button'; closeBtn.className = 'ann-close'; closeBtn.textContent = '✕'; closeBtn.title = '關閉';
  tools.append(editBtn, closeBtn);
  const body = document.createElement('div');
  body.className = 'ann-body';
  const meta = document.createElement('div');
  meta.className = 'ann-meta';
  const editor = document.createElement('div');
  editor.className = 'ann-editor'; editor.hidden = true;
  const quillEl = document.createElement('div');
  quillEl.className = 'ann-quill';
  const editbar = document.createElement('div');
  editbar.className = 'ann-editbar';
  const submit = document.createElement('button');
  submit.type = 'button'; submit.textContent = '送出';
  const cancel = document.createElement('button');
  cancel.type = 'button'; cancel.className = 'ann-cancel'; cancel.textContent = '取消';
  editbar.append(submit, cancel);
  editor.append(quillEl, editbar);
  banner.append(tools, body, meta, editor);
  host.appendChild(banner);

  function dateStr(ts) {
    return (ts && ts.toDate) ? ts.toDate().toLocaleDateString() : '';
  }
  function version() {
    return (data && data.updatedAt && data.updatedAt.toMillis) ? String(data.updatedAt.toMillis()) : '';
  }

  // ---- 渲染（顯示邏輯的單一來源）----
  function render() {
    if (!editor.hidden) return;   // 編輯中不重繪
    editBtn.hidden = !isAdminNow;
    const html = data && data.html ? data.html : '';

    if (!html) {                  // 無公告
      if (isAdminNow) {           // 管理員：顯示空橫幅以便首發
        body.innerHTML = '<em class="ann-empty">（目前沒有公告，按「編輯」發布）</em>';
        meta.textContent = '';
        closeBtn.hidden = true;
        host.hidden = false;
      } else {
        host.hidden = true;
      }
      return;
    }

    // 有公告：一般訪客若已關閉同版則隱藏；管理員永遠看得到
    let dismissed = '';
    try { dismissed = localStorage.getItem('ann-dismissed') || ''; } catch (e) { /* 無 storage */ }
    if (!isAdminNow && version() && dismissed === version()) { host.hidden = true; return; }

    body.innerHTML = DOMPurify.sanitize(html, { ALLOWED_URI_REGEXP: /^(?:https?|mailto):/i });
    const c = dateStr(data.createdAt);
    const u = dateStr(data.updatedAt);
    meta.textContent = c ? ('發布於 ' + c + (u && u !== c ? ' · 編輯於 ' + u : '')) : '';
    closeBtn.hidden = false;
    host.hidden = false;
  }

  closeBtn.onclick = () => {
    if (version()) {
      try { localStorage.setItem('ann-dismissed', version()); } catch (e) { /* 無 storage */ }
    }
    host.hidden = true;
  };

  // ---- 讀取 ----
  async function load() {
    try {
      const snap = await getDoc(doc(db, 'announcements', 'current'));
      data = snap.exists() ? snap.data() : null;
    } catch (e) { data = null; }
    render();
  }

  // ---- 管理員身分 ----
  onAuthChange((user) => {
    isAdminNow = !!(user && isAdmin(user.uid));
    render();
  });

  // ---- 編輯（lazy-load Quill）----
  function ensureQuill() {
    if (window.Quill) return Promise.resolve();
    if (quillLoading) return quillLoading;
    quillLoading = new Promise((resolve, reject) => {
      const css = document.createElement('link');
      css.rel = 'stylesheet'; css.href = 'https://cdn.quilljs.com/1.3.7/quill.snow.css';
      document.head.appendChild(css);
      const s = document.createElement('script');
      s.src = 'https://cdn.quilljs.com/1.3.7/quill.min.js';
      s.onload = resolve;
      s.onerror = () => reject(new Error('Quill 載入失敗'));
      document.head.appendChild(s);
    });
    return quillLoading;
  }

  editBtn.onclick = async () => {
    try { await ensureQuill(); } catch (e) { alert('編輯器載入失敗，請稍後再試'); return; }
    if (!quill) {
      quill = new Quill(quillEl, {
        theme: 'snow',
        modules: {
          toolbar: [
            [{ header: [1, 2, 3, false] }],
            ['bold', 'italic'],
            [{ list: 'ordered' }, { list: 'bullet' }],
            ['link'],
          ],
        },
      });
    }
    quill.clipboard.dangerouslyPasteHTML((data && data.html) || '');
    body.hidden = true; meta.hidden = true; tools.hidden = true;
    editor.hidden = false;
    host.hidden = false;
  };

  function closeEditor() {
    editor.hidden = true;
    body.hidden = false; meta.hidden = false; tools.hidden = false;
    render();
  }
  cancel.onclick = closeEditor;

  submit.onclick = async () => {
    const u = currentUser();
    if (!u || !isAdmin(u.uid)) { alert('沒有權限'); return; }
    const text = quill.getText().trim();
    const html = text ? quill.root.innerHTML : '';   // 全空 → 存空字串（對所有人隱藏公告）
    if (new Blob([html]).size > 50000) { alert('內文過長，請精簡'); return; }
    const payload = { html, updatedAt: serverTimestamp() };
    if (!(data && data.createdAt)) payload.createdAt = serverTimestamp();  // 首發才寫 createdAt
    try {
      await setDoc(doc(db, 'announcements', 'current'), payload, { merge: true });
    } catch (e) { alert('儲存失敗，請稍後再試'); return; }
    try { localStorage.removeItem('ann-dismissed'); } catch (e) { /* 無 storage */ }
    editor.hidden = true;
    body.hidden = false; meta.hidden = false; tools.hidden = false;
    await load();
  };

  load();
}
