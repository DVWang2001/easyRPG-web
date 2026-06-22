# 存檔面板（本機 zip＋雲端備份）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 把導出/導入存檔與新的「雲端上傳/取回」收進一個「存檔」面板；雲端用 Firestore（Bytes）私有備份；`#saveui` 重排成攻略/留言在最右。

**Architecture:** `_SAVE_UI`（內嵌 classic JS）改成「存檔」鈕開 `#savepanel`（內含導出/導入 zip ＋ `#sp-cloud` 容器）並暴露 `window.__epSaves={read,write}`；新模組 `web/savepanel.js` 把雲端 UI 填進 `#sp-cloud`，用 Firestore 讀寫 `users/<uid>/saves`。規則擴充。

**Tech Stack:** Firebase 9.23.0（gstatic CDN，含 `Bytes`）、純前端 ES module、Python build（pwa.py）、pytest。

## Global Constraints

- 設計依據：`docs/superpowers/specs/2026-06-22-cloud-save-design.md`。
- Firebase SDK 固定 `https://www.gstatic.com/firebasejs/9.23.0/firebase-firestore.js`。
- 存檔私有：`users/<uid>/saves/<slug>` 與其 `files/<name>` 只有 `request.auth.uid == uid` 能讀寫。
- 存檔以 Firestore `Bytes` 存（每檔一份文件，≤900KB 才上傳）。
- 手動：上傳＝本機覆蓋雲端、取回＝雲端覆蓋本機，皆先 `confirm`；本機 zip 不需後端。
- `#saveui` 順序（左→右）：`存檔(save-open)`、`❤(fav-btn)`、`已遊玩(pt-label)`、`攻略(wt-open)`、`留言(cm-open)`。
- 假暫停 `block()` 白名單需含 `#wt-panel`、`#cm-panel`、`#savepanel`、`#saveui`（讓面板內輸入/按鍵不被擋；順帶修留言面板打字被擋的舊問題）。
- `web/firebase-config.js`（真實金鑰）維持 gitignored、永不 commit；只動 `firestore.rules`、`savepanel.*`、`pwa.py`、測試。

---

### Task 1: Firestore 規則 — 雲端存檔（私有）

**Files:** Modify `web/firestore.rules`

- [ ] **Step 1: 在 `match /users/{uid}/history/{slug} { ... }` 之後、同層新增**

```
      // 雲端存檔：完全私有，只有本人能讀寫（含 files 子集合）。
      match /users/{uid}/saves/{slug} {
        allow read, write: if request.auth != null && request.auth.uid == uid;
        match /files/{name} {
          allow read, write: if request.auth != null && request.auth.uid == uid;
        }
      }
```

（只新增；既有規則不動。確認大括號層級與 history/favorites 同層，仍在 `match /databases/{database}/documents` 內。）

- [ ] **Step 2: 確認**

Run: `grep -nE "match /users/\{uid\}/saves" web/firestore.rules`
Expected: 顯示 `match /users/{uid}/saves/{slug} {`。

- [ ] **Step 3: Commit**

```bash
git add web/firestore.rules
git commit -m "feat(rules): 雲端存檔私有規則（users/{uid}/saves）"
```

---

### Task 2: 前端 `web/savepanel.js` ＋ `web/savepanel.css`

**Files:** Create `web/savepanel.js`, `web/savepanel.css`

**Interfaces:**
- Consumes: `./account.js`（`db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser`）；Firebase `doc, getDoc, getDocs, setDoc, deleteDoc, collection, serverTimestamp, Bytes`；DOM `#sp-cloud`（Task 3 提供）；`window.__epSaves.read()/write()`（Task 3 提供）；`window.__WT.slug`。

- [ ] **Step 1: 建立 `web/savepanel.css`**

```css
/* 存檔面板：雲端區塊（面板殼與 .sp-btn 由 _SAVE_UI 內嵌樣式提供） */
#sp-cloud .sp-status { color:#9ca3af; font-size:13px; margin:6px 0; }
#sp-cloud .sp-link { background:none; border:1px solid #3a3a3a; color:#cbd5e1;
  border-radius:8px; padding:2px 8px; font-size:12px; cursor:pointer; }
```

- [ ] **Step 2: 建立 `web/savepanel.js`（完整內容）**

```javascript
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
```

- [ ] **Step 3: 語法檢查**

Run: `cp web/savepanel.js _check.mjs && node --check _check.mjs && rm _check.mjs`
Expected: 無輸出。

- [ ] **Step 4: Commit**

```bash
git add web/savepanel.js web/savepanel.css
git commit -m "feat(web): 雲端存檔模組 savepanel.js/css（上傳/取回）"
```

---

### Task 3: `pwa.py` 改「存檔」面板＋暴露 __epSaves＋注入雲端模組，補測試

**Files:** Modify `pwa.py`；Test `tests/test_pwa_gamepages.py`、`tests/test_pwa_webassets.py`

**Interfaces:**
- Produces: 遊戲頁 `window.__epSaves = { read(), write(files) }`、`#save-open`/`#savepanel`/`#sp-cloud`、重排的 `#saveui`、savepanel.js/css 引用。

- [ ] **Step 1: 補/改測試**

在 `tests/test_pwa_gamepages.py`：（a）把既有 `test_write_game_pages_injects_save_ui` 末尾補三行斷言；（b）末尾新增兩個測試。

於 `test_write_game_pages_injects_save_ui` 的 `assert 'SLUG="g"' in html or 'SLUG = "g"' in html` 之後加：

```python
    # 收進單一「存檔」面板：存檔鈕開面板，導出/導入在面板內，雲端容器，暴露 __epSaves
    assert 'id="save-open"' in html and 'id="savepanel"' in html and 'id="sp-cloud"' in html
    assert "window.__epSaves" in html
    # 攻略/留言在最右（DOM 順序在存檔鈕之後）
    assert html.index('id="wt-open"') > html.index('id="save-open"')
    assert html.index('id="cm-open"') > html.index('id="wt-open"')
```

在檔案末尾新增：

```python
def test_write_game_pages_injects_cloudsave(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    pwa.write_game_pages(dist, [{"label": "甲", "slug": "g", "cover_rel": None}])
    html = (dist / "play-g.html").read_text(encoding="utf-8")
    assert 'href="savepanel.css"' in html
    assert 'type="module" src="savepanel.js"' in html
```

- [ ] **Step 2: 在 `tests/test_pwa_webassets.py` 補資產斷言**

把 `test_install_web_assets_copies_js_css` 的名稱元組擴充加入 `"savepanel.js"`, `"savepanel.css"`。將：

```python
    for name in ("account.js", "walkthrough.js", "walkthrough.css",
                 "community.js", "community.css",
                 "favorites.js", "favorites.css", "playtime.js",
                 "profile.js", "profile.css"):
        assert (dist / name).exists(), name
        assert name in copied
```

改成：

```python
    for name in ("account.js", "walkthrough.js", "walkthrough.css",
                 "community.js", "community.css",
                 "favorites.js", "favorites.css", "playtime.js",
                 "profile.js", "profile.css",
                 "savepanel.js", "savepanel.css"):
        assert (dist / name).exists(), name
        assert name in copied
```

- [ ] **Step 3: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_gamepages.py tests/test_pwa_webassets.py -q`
Expected: save_ui/cloudsave 注入測試 FAIL（尚未重構）；webassets 此時應已 PASS（Task 2 已建立 savepanel.*）。

- [ ] **Step 4: 整段替換 `pwa.py` 的 `_SAVE_UI = r"""..."""`**

把 `pwa.py` 中從 `_SAVE_UI = r"""` 到對應結尾 `"""`（含）整段，替換成：

```python
_SAVE_UI = r"""
<style>#saveui{position:fixed;left:8px;top:calc(8px + env(safe-area-inset-top));
z-index:10000;display:flex;gap:6px}
#saveui button{padding:5px 10px;border-radius:8px;border:1px solid #3a3a3a;
background:rgba(31,41,55,.85);color:#cbd5e1;font:12px -apple-system,sans-serif;cursor:pointer}
#saveui button:active{background:#2563eb;color:#fff}
#savepanel{position:fixed;inset:0;z-index:11000}#savepanel[hidden]{display:none}
#savepanel .sp-bd{position:absolute;inset:0;background:rgba(0,0,0,.6)}
#savepanel .sp-dlg{position:relative;max-width:420px;margin:8vh auto;background:#1b1b1b;color:#eee;
border-radius:14px;padding:16px;box-shadow:0 12px 40px rgba(0,0,0,.6);
font-family:-apple-system,"PingFang TC","Microsoft JhengHei",sans-serif}
#savepanel h3{margin:0 0 12px;font-size:16px}
#savepanel .sp-close{position:absolute;top:10px;right:12px;background:none;border:none;color:#cbd5e1;font-size:18px;cursor:pointer}
#savepanel .sp-btn{display:block;width:100%;margin:6px 0;padding:8px 10px;border-radius:8px;
border:1px solid #3a3a3a;background:#1f2937;color:#cbd5e1;font-size:14px;cursor:pointer}
#savepanel .sp-btn:disabled{opacity:.5;cursor:default}
#sp-cloud{margin-top:10px;border-top:1px solid #333;padding-top:10px}</style>
<div id="saveui"><button id="save-open">存檔</button><button id="fav-btn" title="收藏">♡</button><span id="pt-label" style="align-self:center;color:#9ca3af;font:12px -apple-system,sans-serif;padding:0 4px"></span><button id="wt-open">攻略</button><button id="cm-open">留言</button>
<input id="savefile" type="file" accept=".zip" style="display:none"></div>
<div id="savepanel" hidden><div class="sp-bd"></div><div class="sp-dlg">
<button class="sp-close" type="button">✕</button><h3>存檔</h3>
<button id="saveexp" class="sp-btn" type="button">導出存檔（下載 zip）</button>
<button id="saveimp" class="sp-btn" type="button">導入存檔（上傳 zip）</button>
<div id="sp-cloud"></div>
</div></div>
<script>(function(){
var SLUG=__SLUG__;
window.__epPause=window.__epPause||(function(){var keys={},n=0,ctxs=window.__epAudioCtxs=window.__epAudioCtxs||[];
["AudioContext","webkitAudioContext"].forEach(function(nm){var C=window[nm];if(C&&!C.__epW){var W=function(o){var c=new C(o);ctxs.push(c);return c;};W.prototype=C.prototype;W.__epW=1;try{window[nm]=W;}catch(e){}}});
function mute(on){ctxs.forEach(function(c){try{on?c.suspend():c.resume();}catch(e){}});}
function block(e){if(!window.__epPaused)return;var t=e.target;if(t&&t.closest&&(t.closest("#wt-panel")||t.closest("#cm-panel")||t.closest("#savepanel")||t.closest("#saveui")))return;e.stopImmediatePropagation();e.preventDefault();}
["keydown","keyup","keypress"].forEach(function(ev){window.addEventListener(ev,block,true);});
return function(on,key){key=key||"_";if(on){if(!keys[key]){keys[key]=1;if(++n===1){window.__epPaused=true;mute(true);}}}else{if(keys[key]){delete keys[key];if(--n===0){window.__epPaused=false;mute(false);}}}};})();
var ui=document.getElementById("saveui"),inp=document.getElementById("savefile");
function mod(){try{return (typeof easyrpgPlayer!=="undefined"&&easyrpgPlayer&&easyrpgPlayer.FS)?easyrpgPlayer:null;}catch(e){return null;}}
function vis(){ui.style.display=(document.fullscreenElement||document.webkitFullscreenElement)?"none":"flex";}
document.addEventListener("fullscreenchange",vis);
document.addEventListener("webkitfullscreenchange",vis);vis();
function isLsd(n){return /^Save\d+\.lsd$/i.test(n);}
function guessDir(){var m=mod();var g=((m&&m.game)||SLUG||"").toLowerCase();return "/easyrpg/"+g+"/Save";}
function isDir(FS,p){try{return FS.isDir(FS.stat(p).mode);}catch(e){return false;}}
function hasLsd(FS,p){try{return FS.readdir(p).some(isLsd);}catch(e){return false;}}
function walkDir(FS){var skip={"/dev":1,"/proc":1,"/tmp":1,"/home":1},q=["/"],seen={};
while(q.length){var d=q.shift();if(seen[d])continue;seen[d]=1;var ents;try{ents=FS.readdir(d);}catch(e){continue;}
var hit=false;for(var i=0;i<ents.length;i++){var n=ents[i];if(n==="."||n==="..")continue;
if(isLsd(n)){hit=true;continue;}var p=(d==="/"?"":d)+"/"+n;if(!skip[p]&&isDir(FS,p))q.push(p);}
if(hit)return d;}return null;}
function saveDir(FS,forImport){var g=guessDir();
if(hasLsd(FS,g))return g;var w=walkDir(FS);if(w)return w;
return forImport&&isDir(FS,g)?g:null;}
function mkdirp(FS,p){var parts=p.split("/").filter(Boolean),cur="";
for(var i=0;i<parts.length;i++){cur+="/"+parts[i];try{FS.mkdir(cur);}catch(e){}}}
function crc32T(){var t=[];for(var n=0;n<256;n++){var c=n;for(var k=0;k<8;k++)c=(c&1)?(0xEDB88320^(c>>>1)):(c>>>1);t[n]=c>>>0;}return t;}
var crcT=crc32T();
function crc32(u){var c=0xFFFFFFFF;for(var i=0;i<u.length;i++)c=crcT[(c^u[i])&0xFF]^(c>>>8);return (c^0xFFFFFFFF)>>>0;}
function te(s){return new TextEncoder().encode(s);}
function u32(v){return [v&255,(v>>>8)&255,(v>>>16)&255,(v>>>24)&255];}
function u16(v){return [v&255,(v>>>8)&255];}
function readSaves(){var FS=mod().FS,dir=saveDir(FS,false),out=[];if(!dir)return out;
FS.readdir(dir).forEach(function(n){if(n==="."||n==="..")return;try{if(isDir(FS,dir+"/"+n))return;
var d=FS.readFile(dir+"/"+n);if(d&&d.length)out.push({name:n,data:d});}catch(e){}});return out;}
function makeZip(files){var parts=[],central=[],offset=0;
files.forEach(function(f){var nameB=te(f.name),crc=crc32(f.data),sz=f.data.length;
var lh=[].concat(u32(0x04034b50),u16(20),u16(0),u16(0),u16(0),u16(0),u32(crc),u32(sz),u32(sz),u16(nameB.length),u16(0));
parts.push(new Uint8Array(lh));parts.push(nameB);parts.push(f.data);
var ch=[].concat(u32(0x02014b50),u16(20),u16(20),u16(0),u16(0),u16(0),u16(0),u32(crc),u32(sz),u32(sz),u16(nameB.length),u16(0),u16(0),u16(0),u16(0),u32(0),u32(offset));
central.push(new Uint8Array(ch));central.push(nameB);
offset+=lh.length+nameB.length+sz;});
var cs=0;central.forEach(function(p){cs+=p.length;});
var eocd=new Uint8Array([].concat(u32(0x06054b50),u16(0),u16(0),u16(files.length),u16(files.length),u32(cs),u32(offset),u16(0)));
var all=parts.concat(central);all.push(eocd);var total=0;all.forEach(function(p){total+=p.length;});
var buf=new Uint8Array(total),o=0;all.forEach(function(p){buf.set(p,o);o+=p.length;});return buf;}
function readZip(u){var dv=new DataView(u.buffer,u.byteOffset,u.byteLength),i=0,files=[];
while(i+4<=u.length&&dv.getUint32(i,true)===0x04034b50){
var nlen=dv.getUint16(i+26,true),elen=dv.getUint16(i+28,true),csz=dv.getUint32(i+18,true);
var name=new TextDecoder().decode(u.slice(i+30,i+30+nlen)),ds=i+30+nlen+elen;
files.push({name:name,data:u.slice(ds,ds+csz)});i=ds+csz;}return files;}
window.__epSaves={read:function(){return mod()?readSaves():[];},
write:function(files){return new Promise(function(res,rej){var m=mod();if(!m){rej(new Error("遊戲尚未載入"));return;}
try{var FS=m.FS,dir=saveDir(FS,true)||guessDir();mkdirp(FS,dir);
files.forEach(function(fl){FS.writeFile(dir+"/"+fl.name,fl.data);});
FS.syncfs(false,function(){res();});}catch(e){rej(e);}});}};
var panel=document.getElementById("savepanel");
document.getElementById("save-open").onclick=function(){if(!mod()){alert("遊戲尚未載入完成，請稍候");return;}panel.hidden=false;window.__epPause(true,"save");};
function spClose(){panel.hidden=true;window.__epPause(false,"save");}
panel.querySelector(".sp-close").onclick=spClose;panel.querySelector(".sp-bd").onclick=spClose;
document.getElementById("saveexp").onclick=function(){window.__epPause(true,"exp");try{
var m=mod();if(!m){alert("遊戲尚未載入完成，請稍候");return;}
var files=readSaves();if(!files.length){alert("找不到存檔（請先在遊戲裡存檔）");return;}
var blob=new Blob([makeZip(files)],{type:"application/zip"});
var a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download=SLUG+"-saves.zip";a.click();
setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},1000);
}finally{window.__epPause(false,"exp");}};
document.getElementById("saveimp").onclick=function(){if(!mod()){alert("遊戲尚未載入完成，請稍候");return;}
window.__epPause(true,"imp");
function done(){window.removeEventListener("focus",onFocus);window.__epPause(false,"imp");}
function onFocus(){setTimeout(done,300);}
window.addEventListener("focus",onFocus);inp.oncancel=done;
inp.click();};
inp.onchange=function(){window.__epPause(false,"imp");var f=inp.files[0];if(!f)return;var r=new FileReader();
r.onload=function(){try{var files=readZip(new Uint8Array(r.result));if(!files.length){alert("檔案內沒有存檔");return;}
var FS=mod().FS,dir=saveDir(FS,true)||guessDir();mkdirp(FS,dir);
files.forEach(function(fl){FS.writeFile(dir+"/"+fl.name,fl.data);});
FS.syncfs(false,function(){alert("已導入 "+files.length+" 個存檔，將重新載入遊戲。");location.reload();});
}catch(e){alert("導入失敗："+e);}};r.readAsArrayBuffer(f);inp.value="";};
})();</script>
"""
```

- [ ] **Step 5: 新增 `_CLOUD_SNIPPET` 並接到 `body_add`**

在 `pwa.py` 的 `_PT_SNIPPET = """..."""` 定義之後，新增：

```python
# 雲端存檔：純前端模組（填進 _SAVE_UI 的 #sp-cloud；用 window.__epSaves 與 window.__WT.slug）。
_CLOUD_SNIPPET = """
<link rel="stylesheet" href="savepanel.css">
<script type="module" src="savepanel.js"></script>
"""
```

接著找到（playtime 完成後的版本）：

```python
        body_add = dl_snippet + save_snippet + wt_snippet + _CM_SNIPPET + _FAV_SNIPPET + _PT_SNIPPET
```

改成：

```python
        body_add = dl_snippet + save_snippet + wt_snippet + _CM_SNIPPET + _FAV_SNIPPET + _PT_SNIPPET + _CLOUD_SNIPPET
```

- [ ] **Step 6: 驗證注入 JS 語法**

Run: `python -c "import re,pwa;m=re.search(r'<script>(.*)</script>',pwa._SAVE_UI.replace('__SLUG__','\"g\"'),re.S);open('_s.mjs','w',encoding='utf-8').write(m.group(1))"` 然後 `node --check _s.mjs && rm _s.mjs`
Expected: 無輸出（內嵌 JS 語法正確）。

- [ ] **Step 7: 跑測試**

Run: `python -m pytest tests/test_pwa_gamepages.py tests/test_pwa_webassets.py -q`
Expected: PASS。

- [ ] **Step 8: 全測試**

Run: `python -m pytest tests/ -q`
Expected: 全部 PASS。

- [ ] **Step 9: Commit**

```bash
git add pwa.py tests/test_pwa_gamepages.py tests/test_pwa_webassets.py
git commit -m "feat(pwa): 存檔面板整合導出/導入＋雲端，暴露 __epSaves，攻略/留言移最右"
```

---

## 收尾：手動驗證

- [ ] 重建並部署，且 Firestore 規則**重新發布**（本輪規則為擴充）。
- [ ] `#saveui` 順序：存檔、❤、已遊玩、攻略、留言（攻略/留言最右）。
- [ ] 點「存檔」→ 面板：導出/導入 zip 同現況；遊戲暫停、不黑。
- [ ] 登入→上傳→另一裝置/無痕取回→遊戲帶到該存檔；未登入雲端區塊提示登入、zip 仍可用。上傳/取回前確認。
- [ ] 留言面板打字正常（block 白名單已含 #cm-panel）。

## Self-Review 註記（已檢查）
- **Spec 覆蓋**：規則(Task1)、savepanel.js 上傳/取回/狀態/登入/!isReady(Task2)、_SAVE_UI 收進面板＋__epSaves＋重排＋block 白名單＋注入(Task3)、資產複製(Task3 webassets)——皆有對應。
- **型別一致**：`window.__epSaves.{read,write}` 在 Task3 定義、Task2 使用一致；`#sp-cloud`/`#save-open`/`#savepanel` 在 Task3 模板與 Task2/測試一致；Firestore 路徑 `users/<uid>/saves/<slug>(/files/<name>)` 與規則一致；欄位 `{data:Bytes,updatedAt}`、父 `{updatedAt,names}`。
- **行為不變**：導出/導入 zip 邏輯原封不動（只移進面板）；既有 save_ui 測試大部分斷言仍成立，僅補新斷言。
