// 雲端存檔：把雲端 UI 填進「存檔」面板的 #sp-cloud。用 _SAVE_UI 暴露的 window.__epSaves 與地基 account.js。
// 登入後全自動同步（背景自動上傳／悄悄拉回較新版本），只有本機與雲端互相衝突時才問一次；
// 手動按鈕保留，供「立即同步」或自動同步失敗時排解問題用。
import {
  doc, getDoc, getDocs, setDoc, collection, serverTimestamp, Bytes, writeBatch,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser,
} from './account.js';

const SLUG = (window.__WT && window.__WT.slug) || '';
const box = document.getElementById('sp-cloud');
const MAXBYTES = 900 * 1024;
const SYNC_KEY = 'ep-savesync-' + SLUG;

// 指紋＝檔名+大小的排序清單字串化。存檔通常很小，size+name 已足夠當變更信號，
// 不用算內容雜湊；跟建置期 games/ 的內容版本雜湊（staging.content_version，供瀏覽器快取失效用）
// 是不同機制、各自獨立，這裡只管存檔同步。
function fingerprint(files) {
  return JSON.stringify(
    files.map((f) => ({ name: f.name, size: f.data.length }))
      .sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0)),
  );
}
function syncableFiles() {
  const files = window.__epSaves ? window.__epSaves.read() : [];
  return files.filter((f) => f.data.length <= MAXBYTES);
}
function lastSyncedFp() {
  try { return localStorage.getItem(SYNC_KEY); } catch (e) { return null; }
}
function setSyncedFp(fp) {
  try {
    if (fp) localStorage.setItem(SYNC_KEY, fp); else localStorage.removeItem(SYNC_KEY);
  } catch (e) { /* 私密瀏覽等環境可能擋 localStorage，忽略即可 */ }
}

if (box) build();

function build() {
  const status = document.createElement('div');
  status.className = 'sp-status'; status.textContent = '雲端存檔';
  const auth = document.createElement('div');
  auth.className = 'sp-status';
  const up = document.createElement('button');
  up.type = 'button'; up.className = 'sp-btn'; up.textContent = '立即上傳';
  const down = document.createElement('button');
  down.type = 'button'; down.className = 'sp-btn'; down.textContent = '立即取回';
  box.append(status, auth, up, down);

  if (!isReady()) {
    status.textContent = '雲端功能需站長設定後端';
    up.disabled = true; down.disabled = true;
    return;
  }

  // ---- 共用的上傳/下載邏輯：手動按鈕與自動同步都走這兩支 ----
  // 上傳合併成單一 batch commit（1 次讀現有檔案清單 + 1 次批次寫入），
  // 不再是「每個檔案一次 setDoc + 一次 getDocs + 多次 deleteDoc + 一次 setDoc」的序列 await——
  // 那樣在 visibilitychange/pagehide（分頁關閉時）很容易還沒送到 Firestore 就被中斷。
  async function uploadFiles(uid, files) {
    const names = files.map((f) => f.name);
    const snap = await getDocs(collection(db, 'users', uid, 'saves', SLUG, 'files'));
    const batch = writeBatch(db);
    for (const f of files) {
      batch.set(doc(db, 'users', uid, 'saves', SLUG, 'files', f.name),
        { data: Bytes.fromUint8Array(f.data), updatedAt: serverTimestamp() });
    }
    for (const d of snap.docs) { if (!names.includes(d.id)) batch.delete(d.ref); }
    const fp = fingerprint(files);
    batch.set(doc(db, 'users', uid, 'saves', SLUG),
      { updatedAt: serverTimestamp(), names, fp });
    await batch.commit();
    setSyncedFp(fp);
    return names;
  }

  async function downloadAndApply(uid, names) {
    const files = [];
    for (const name of names) {
      const fsnap = await getDoc(doc(db, 'users', uid, 'saves', SLUG, 'files', name));
      if (fsnap.exists() && fsnap.data().data) {
        files.push({ name, data: fsnap.data().data.toUint8Array() });
      }
    }
    if (!files.length) return false;
    await window.__epSaves.write(files);
    setSyncedFp(fingerprint(files));
    return true;
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
      autoSyncOnLoad(u.uid);
    } else {
      const b = document.createElement('button');
      b.type = 'button'; b.className = 'sp-link'; b.textContent = '用 Google 登入';
      b.onclick = () => signInWithGoogle().catch(() => alert('登入失敗'));
      auth.append(b);
      status.textContent = '登入後自動雲端備份';
    }
  }
  onAuthChange(renderAuth);

  async function loadStatus(uid) {
    try {
      const snap = await getDoc(doc(db, 'users', uid, 'saves', SLUG));
      const t = snap.exists() && snap.data().updatedAt && snap.data().updatedAt.toDate
        ? snap.data().updatedAt.toDate().toLocaleString() : null;
      status.textContent = t ? ('已自動同步（上次：' + t + '）') : '尚未備份';
    } catch (e) { status.textContent = '雲端狀態載入失敗'; }
  }

  // ---- 開頁自動同步：本機／雲端／上次同步點 三方比較，只有真衝突才問 ----
  let autoBusy = false;
  async function autoSyncOnLoad(uid) {
    if (autoBusy) return;
    autoBusy = true;
    try {
      const localFiles = syncableFiles();
      const localFp = fingerprint(localFiles);
      const lastFp = lastSyncedFp();
      const parent = await getDoc(doc(db, 'users', uid, 'saves', SLUG));
      const cloudFp = parent.exists() ? (parent.data().fp || null) : null;
      const cloudNames = (parent.exists() && parent.data().names) || [];

      if (localFp === cloudFp) {
        if (!lastFp) setSyncedFp(localFp);
        return;
      }
      if (!cloudNames.length) return; // 雲端沒有存檔，之後自動上傳即可
      if (!localFiles.length || lastFp === localFp) {
        // 本機沒東西可丟，或本機自上次同步後沒變 → 雲端較新，悄悄拉回
        if (await downloadAndApply(uid, cloudNames)) location.reload();
        return;
      }
      if (lastFp === cloudFp) return; // 雲端自上次同步後沒變、本機較新 → 交給自動上傳
      // 兩邊都變了而且不一樣 → 唯一需要問使用者的情況
      if (confirm('這款遊戲在雲端和這台裝置都有新的存檔進度，要用哪一邊？\n'
                  + '「確定」＝用雲端蓋掉本機　「取消」＝保留本機（稍後自動上傳覆蓋雲端）')) {
        if (await downloadAndApply(uid, cloudNames)) location.reload();
      } else {
        setSyncedFp(localFp);
      }
    } catch (e) { /* 自動同步失敗就算了，不打擾使用者；下次開頁再試 */ }
    autoBusy = false;
  }

  // ---- 本機有變化才自動上傳：前景定時檢查為主，關頁/切走當最後防線 ----
  // 只靠 visibilitychange/pagehide 觸發不可靠（分頁被關閉時，非同步的 Firestore
  // 請求不保證能跑完）；改成分頁還活著、有充裕時間完成網路請求時就先傳，
  // hide/pagehide 只補救「定時器還沒抓到就離開」的最後幾十秒空窗。
  let uploadBusy = false;
  async function maybeAutoUpload() {
    const u = currentUser();
    if (!u || uploadBusy) return;
    const files = syncableFiles();
    if (!files.length) return;
    if (fingerprint(files) === lastSyncedFp()) return;
    uploadBusy = true;
    try { await uploadFiles(u.uid, files); } catch (e) { /* 失敗就算了，下次再試 */ }
    uploadBusy = false;
  }
  setInterval(() => {
    if (document.visibilityState === 'visible') maybeAutoUpload();
  }, 30000);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') maybeAutoUpload();
  });
  window.addEventListener('pagehide', maybeAutoUpload);

  // ---- 手動按鈕：立即同步／自動同步失敗時的排解手段 ----
  up.onclick = async () => {
    const u = currentUser();
    if (!u) { signInWithGoogle().catch(() => alert('登入失敗')); return; }
    const all = window.__epSaves ? window.__epSaves.read() : [];
    if (!all.length) { alert('找不到本機存檔（請先在遊戲裡存檔）'); return; }
    const files = all.filter((f) => f.data.length <= MAXBYTES);
    const skipped = all.length - files.length;
    if (!confirm('上傳會用本機存檔覆蓋雲端，確定？'
                 + (skipped ? ('\n（將略過 ' + skipped + ' 個過大的存檔）') : ''))) return;
    up.disabled = true;
    try {
      const names = await uploadFiles(u.uid, files);
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
      const ok = await downloadAndApply(u.uid, names);
      if (!ok) { alert('雲端沒有存檔'); down.disabled = false; return; }
      alert('已從雲端取回存檔，將重新載入遊戲。');
      location.reload();
    } catch (e) { alert('取回失敗，請稍後再試'); down.disabled = false; }
  };
}
