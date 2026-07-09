// 無感雲端存檔同步：逐槽三方合併＋開機閘門＋存檔即推（syncfs hook）＋onSnapshot 即拉。
// UI＝狀態指示器 #cloud-ind：健康時隱藏；未登入「☁ 同步」；連續失敗「☁⚠」開維修面板。
// spec: docs/superpowers/specs/2026-07-10-seamless-cloud-save-design.md
import {
  doc, getDoc, getDocs, collection, onSnapshot, serverTimestamp, Bytes, writeBatch,
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js';
import {
  db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser,
} from './account.js';
import { decideSlots } from './savemerge.js';

const SLUG = (window.__WT && window.__WT.slug) || '';
const MAXBYTES = 900 * 1024;
const KEY = 'ep-savesync-' + SLUG;
const gate = window.__epGate || { open() {} };
const ind = document.getElementById('cloud-ind');

const mdoc = (uid) => doc(db, 'users', uid, 'saves', SLUG);
const fdoc = (uid, name) => doc(db, 'users', uid, 'saves', SLUG, 'files', name);

// ---- 上次同步指紋：逐槽 JSON map（舊版整組字串讀到就當沒有） ----
function lastMap() {
  try {
    const v = JSON.parse(localStorage.getItem(KEY));
    return (v && typeof v === 'object' && !Array.isArray(v)) ? v : {};
  } catch (e) { return {}; }
}
function setLastMap(m) {
  try { localStorage.setItem(KEY, JSON.stringify(m)); } catch (e) { /* 私密瀏覽等，忽略 */ }
}

// ---- 兩邊槽位快照 ----
function localSlots() {
  const out = {};
  for (const f of window.__epSaves.read()) {
    if (f.data.length > MAXBYTES) continue;
    out[f.name] = { fp: window.__epSaves.fp(f.data), mtime: f.mtime || 0, data: f.data };
  }
  return out;
}
// manifest → { 檔名: {fp, updatedAt 毫秒} }。舊格式（只有 names 沒有 slots）給
// 永不相符的 fp，逼每槽走「雙邊衝突比時間」，同步完成後 manifest 會被改寫成新格式。
function cloudSlots(m) {
  const at = (t, fb) => (t && t.toMillis ? t.toMillis() : fb);
  const base = m ? at(m.updatedAt, 0) : 0;
  const out = {};
  if (m && m.slots) {
    for (const n of Object.keys(m.slots)) {
      out[n] = { fp: m.slots[n].fp, updatedAt: at(m.slots[n].updatedAt, base) };
    }
  } else if (m && m.names) {
    for (const n of m.names) out[n] = { fp: ' legacy', updatedAt: base };
  }
  return out;
}

// ---- 同步核心：一次 sync＝decideSlots 決策 → 拉/推/刪 ----
// manifest 參數語意：物件＝雲端現況（{}＝雲端沒東西）；null＝雲端狀態未知 → 不動作。
let syncing = false;
let pendingManifest;      // sync 進行中又來新 manifest → 收尾後補跑一輪
let seenManifest = null;  // onSnapshot 維持的最新 manifest；即推直接用，免重讀

async function sync(uid, manifest) {
  if (manifest === null) return;                    // 雲端狀態未知，寧可不同步也不能誤刪
  if (syncing) { pendingManifest = manifest; return; }
  syncing = true;
  try {
    const local = localSlots();
    const legacy = !!(manifest.names && !manifest.slots);
    const cloud = cloudSlots(manifest);
    const d = decideSlots(
      Object.fromEntries(Object.entries(local).map(([n, v]) => [n, { fp: v.fp, mtime: v.mtime }])),
      cloud, lastMap(),
    );

    if (d.pull.length) {
      const files = [];
      for (const n of d.pull) {
        const s = await getDoc(fdoc(uid, n));
        if (s.exists() && s.data().data) files.push({ name: n, data: s.data().data.toUint8Array() });
      }
      if (files.length) await window.__epSaves.write(files);
      for (const f of files) local[f.name] = { fp: window.__epSaves.fp(f.data), mtime: Date.now(), data: f.data };
    }
    if (d.deleteLocal.length) {
      await window.__epSaves.remove(d.deleteLocal);
      for (const n of d.deleteLocal) delete local[n];
    }
    if (d.push.length || d.deleteCloud.length || legacy) {
      const batch = writeBatch(db);
      for (const n of d.push) {
        batch.set(fdoc(uid, n), { data: Bytes.fromUint8Array(local[n].data), updatedAt: serverTimestamp() });
      }
      for (const n of d.deleteCloud) batch.delete(fdoc(uid, n));
      // manifest＝合併後的完整逐槽狀態（整份覆寫：槽缺席即代表刪除）。
      // 沒推的槽原樣回寫原 Timestamp，不虛增時間（避免未來衝突比較不公平）。
      const slots = {};
      for (const n of Object.keys(local)) {
        const kept = !d.push.includes(n) && manifest.slots && manifest.slots[n];
        slots[n] = kept || { fp: local[n].fp, updatedAt: serverTimestamp() };
      }
      batch.set(mdoc(uid), { updatedAt: serverTimestamp(), slots });
      await batch.commit();
    }
    // 同步點＝合併完成後兩邊一致的每槽指紋
    setLastMap(Object.fromEntries(Object.keys(local).map((n) => [n, local[n].fp])));
    ok();
  } catch (e) { fail(e); }
  syncing = false;
  if (pendingManifest !== undefined) {
    const m = pendingManifest; pendingManifest = undefined; sync(uid, m);
  }
}

// ---- 存檔即推：引擎存檔後會從 C++ 呼叫 FS.syncfs，包一層當「剛存檔」訊號 ----
function hookSyncfs(FS) {
  if (FS.__epHooked) return;
  FS.__epHooked = true;
  const orig = FS.syncfs.bind(FS);
  FS.syncfs = function (populate, cb) {
    if (typeof populate === 'function') { cb = populate; populate = false; }
    return orig(populate, (err) => {
      if (cb) cb(err);
      if (!populate && !err && !syncing) queuePush();
    });
  };
}
let pushTimer = 0;
function queuePush() {
  if (!currentUser()) return;
  clearTimeout(pushTimer);
  pushTimer = setTimeout(flushPush, 3000); // 去抖：連續存檔只傳一次
}
function flushPush() {
  clearTimeout(pushTimer); pushTimer = 0;
  const u = currentUser();
  if (u && window.__epSaves.ready()) sync(u.uid, seenManifest);
}
// 關頁/切走＝最後防線（盡力而為；平時去抖 3 秒內就已送出）
window.addEventListener('pagehide', flushPush);
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') flushPush();
});

// ---- 雲端即拉：onSnapshot 常駐監聽 manifest ----
let unsub = null;
function attachSnap(uid) {
  if (unsub) return;
  unsub = onSnapshot(mdoc(uid), (snap) => {
    seenManifest = snap.exists() ? snap.data() : {};
    whenEngineReady(() => sync(uid, seenManifest));
  }, (e) => fail(e));
}
function stopSnap() { if (unsub) { unsub(); unsub = null; } }

function whenEngineReady(cb) {
  (function poll() {
    if (window.__epSaves && window.__epSaves.ready()) cb();
    else setTimeout(poll, 200);
  })();
}

// ---- 開機流程：閘門扣住引擎 → 讀 manifest → 放行 → populate 完成後套用 ----
async function bootSync(uid) {
  let m = null;
  try {
    const snap = await getDoc(mdoc(uid));
    m = snap.exists() ? snap.data() : {};
  } catch (e) { /* fail-open：雲端讀不到照樣開機 */ }
  gate.open();
  seenManifest = m;
  whenEngineReady(() => {
    const FS = window.__epSaves.fs();
    // 自己再跑一次 populate（冪等，Task 1 V4 已驗證），確保 IDBFS→記憶體完成
    // 後才套用雲端槽，否則首次 populate 可能把剛寫入的雲端槽蓋回舊檔。
    FS.syncfs(true, () => {
      hookSyncfs(FS);
      sync(uid, seenManifest);
      attachSnap(uid);
    });
  });
}

// ---- UI：按鈕＝狀態指示器 ----
let failCount = 0;
let lastErr = '';
function showLogin() {
  ind.hidden = false; ind.textContent = '☁ 同步'; ind.title = '登入後跨裝置同步存檔';
  ind.onclick = () => signInWithGoogle().catch(() => alert('登入失敗'));
}
function ok() {
  failCount = 0;
  if (currentUser()) ind.hidden = true;
}
function fail(e) {
  lastErr = String((e && e.message) || e);
  if (++failCount < 3) return; // 偶發失敗靜默重試，連續失敗才打擾
  ind.hidden = false; ind.textContent = '☁⚠'; ind.title = '存檔同步異常，點擊處理';
  ind.onclick = () => { renderRepair(); if (window.__epSavePanel) window.__epSavePanel.open(); };
}

// ---- 維修面板：只有連續失敗才看得到的救援通道 ----
function renderRepair() {
  const box = document.getElementById('sp-cloud');
  if (!box) return;
  box.innerHTML = '';
  const st = document.createElement('div');
  st.className = 'sp-status';
  st.textContent = '自動同步連續失敗：' + lastErr;
  const up = document.createElement('button');
  up.type = 'button'; up.className = 'sp-btn'; up.textContent = '立即上傳（本機蓋雲端）';
  const down = document.createElement('button');
  down.type = 'button'; down.className = 'sp-btn'; down.textContent = '立即取回（雲端蓋本機）';
  const out = document.createElement('button');
  out.type = 'button'; out.className = 'sp-link'; out.textContent = '登出';
  out.onclick = () => signOutUser();
  box.append(st, up, down, out);

  up.onclick = async () => {
    const u = currentUser();
    if (!u || !window.__epSaves.ready()) { alert('遊戲尚未載入完成'); return; }
    up.disabled = true;
    try {
      const local = localSlots();
      const batch = writeBatch(db);
      const slots = {};
      for (const n of Object.keys(local)) {
        batch.set(fdoc(u.uid, n), { data: Bytes.fromUint8Array(local[n].data), updatedAt: serverTimestamp() });
        slots[n] = { fp: local[n].fp, updatedAt: serverTimestamp() };
      }
      const snap = await getDocs(collection(db, 'users', u.uid, 'saves', SLUG, 'files'));
      for (const dref of snap.docs) if (!(dref.id in local)) batch.delete(dref.ref);
      batch.set(mdoc(u.uid), { updatedAt: serverTimestamp(), slots });
      await batch.commit();
      setLastMap(Object.fromEntries(Object.keys(local).map((n) => [n, local[n].fp])));
      ok(); alert('已上傳到雲端');
    } catch (e) { alert('上傳失敗：' + e); }
    up.disabled = false;
  };
  down.onclick = async () => {
    const u = currentUser();
    if (!u || !window.__epSaves.ready()) { alert('遊戲尚未載入完成'); return; }
    down.disabled = true;
    try {
      const snap = await getDocs(collection(db, 'users', u.uid, 'saves', SLUG, 'files'));
      const files = [];
      for (const dref of snap.docs) {
        const dd = dref.data();
        if (dd && dd.data) files.push({ name: dref.id, data: dd.data.toUint8Array() });
      }
      if (!files.length) { alert('雲端沒有存檔'); } else {
        await window.__epSaves.write(files);
        setLastMap(Object.fromEntries(files.map((f) => [f.name, window.__epSaves.fp(f.data)])));
        ok(); alert('已取回 ' + files.length + ' 個存檔');
      }
    } catch (e) { alert('取回失敗：' + e); }
    down.disabled = false;
  };
}

// ---- 進入點 ----
if (!SLUG || !ind || !isReady()) {
  gate.open(); // 未設定後端/不在遊戲頁 → 立即放行，全功能停用
} else {
  let booted = false;
  onAuthChange((u) => {
    if (!u) { gate.open(); stopSnap(); showLogin(); return; }
    ind.hidden = failCount < 3; // 登入即隱藏（故障浮現狀態除外）
    if (booted) { attachSnap(u.uid); return; }
    booted = true;
    bootSync(u.uid);
  });
}
