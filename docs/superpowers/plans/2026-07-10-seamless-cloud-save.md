# 無感跨裝置存檔同步 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 登入後遊戲存檔跨裝置全自動同步——零按鈕、零對話框、零 reload；不登入一切如舊。

**Architecture:** 逐槽三方合併（純函式 `decideSlots`）＋開機閘門（包住 MODULARIZE 工廠 `createEasyRpgPlayer`，等雲端 manifest 到手才放行引擎）＋存檔即推（包 `FS.syncfs` 當「剛存檔」訊號）＋`onSnapshot` 即拉。UI 改為狀態指示器：健康時隱藏、未登入「☁ 同步」、連續失敗「☁⚠」開維修面板。zip 導出／導入搬進「下載」面板。

**Tech Stack:** 靜態網站＋Firebase（Firestore 9.23.0 CDN modular、Google 登入，`web/account.js` 地基不動）；建置端 Python（`pwa.py`）＋pytest；純函式測試用 `node --test`（node ≥ 18，機器上是 v20）。

**Spec:** `docs/superpowers/specs/2026-07-10-seamless-cloud-save-design.md`

## Global Constraints

- 不新增任何 npm/pip 相依；Firebase 一律 `https://www.gstatic.com/firebasejs/9.23.0/` CDN modular import。
- `pwa.py` 內嵌的 `_SAVE_UI` 是 classic script，維持 ES5 風格（`var`/`function`，不用箭頭函式）；`web/*.js` module 檔可用現代語法。
- 單檔存檔上限 `MAXBYTES = 900 * 1024`，超過略過不同步（沿用）。
- Firestore 路徑不變：`users/<uid>/saves/<slug>`（manifest）與 `users/<uid>/saves/<slug>/files/<檔名>`；安全規則不動。
- 開機閘門超時 **2000ms**，一律 fail-open：雲端任何問題絕不能擋玩遊戲。
- 同步失敗不彈窗；**連續 3 次**失敗才浮現「☁⚠」。
- 存檔即推去抖 **3000ms**。
- 所有 commit 只 `git add` 該任務點名的檔案（working tree 有大量不相干的未 commit 修改，不許夾帶）。
- 工作分支：`feat/seamless-cloudsave`（從 main 建）。
- pytest 指令：`python -m pytest tests/ -q`；node 測試指令：`node --test tests/test_savemerge.mjs`。
- **注意**：`web/savepanel.js` 現有 +135 行未 commit 的舊版自動同步（整組指紋），依已定案決策**直接整檔重寫、不保留**。

## File Structure

| 檔案 | 動作 | 責任 |
|---|---|---|
| `web/savemerge.js` | 新增 | 逐槽三方合併決策，純函式、零相依（瀏覽器與 node 共用） |
| `web/package.json` | 新增 | `{"type":"module"}`，讓 node 把 `web/*.js` 當 ESM（瀏覽器無視；`install_web_assets` 只複製 .js/.css/.woff2/.png，不會進 dist） |
| `tests/test_savemerge.mjs` | 新增 | `decideSlots` 的 node --test 單元測試 |
| `pwa.py` | 修改 | `_SAVE_UI` 重構（`__epSaves` 擴充、按鈕搬家、雙面板）＋新增 `_GATE_SNIPPET` 開機閘門 |
| `tests/test_pwa_gamepages.py` | 修改 | 對應的產出 HTML 斷言 |
| `web/savepanel.js` | 重寫 | 同步引擎全部：開機閘門開閘、逐槽 sync、syncfs hook、onSnapshot、指示器＋維修面板 |

---

### Task 1: 時序假設驗證（手動 runbook）

**Files:** 無程式碼變更；產出＝驗證結果記錄（貼在本檔案末尾的「Task 1 結果」區塊並 commit）。

**Interfaces:**
- Produces: V1–V4 的 PASS/FAIL 結論。**任一 FAIL → 停下回報**，依「決策表」調整後續任務，不得逕行實作主路線。

- [ ] **Step 1: 起本地伺服器並開一款遊戲**

```powershell
python -m http.server 8000 --directory C:\opensource\easyRPG-web\dist
```

瀏覽器開 `http://localhost:8000/`，進任一遊戲頁（記下 slug）。Firebase 預設授權網域含 localhost，登入功能可用（本任務不需登入）。

- [ ] **Step 2: V1——引擎存檔會呼叫 FS.syncfs**

等遊戲載入完，DevTools console 貼：

```js
var FS = easyrpgPlayer.FS, orig = FS.syncfs.bind(FS);
FS.syncfs = function(p, cb){ if (typeof p === 'function'){ cb = p; p = false; } console.log('EP syncfs, populate =', p); return orig(p, cb); };
```

遊戲內存一次檔。**Expected: console 出現 `EP syncfs, populate = false`。**

- [ ] **Step 3: V2——讀檔選單重掃存檔資料夾**

存檔後回到地圖，console 貼（`<slug>` 換成實際值；路徑不確定就先跑 `window.__epSaves.read()` 看檔名、用 `easyrpgPlayer.FS.readdir` 探）：

```js
var d = '/easyrpg/<slug>/Save', FS = easyrpgPlayer.FS;
FS.writeFile(d + '/Save02.lsd', FS.readFile(d + '/Save01.lsd'));
```

開遊戲內「讀檔」選單。**Expected: 槽 2 出現剛複製的進度，不用重新整理頁面。**

- [ ] **Step 4: V3——createEasyRpgPlayer 包裝攔得住引擎啟動**

直接編輯 `dist/play-<slug>.html`（僅本機實驗，不 commit），在 `</head>` 前貼：

```html
<script>(function(){var open,p=new Promise(function(r){open=r;});
window.__epGate={done:p,open:open};
var real=null;
Object.defineProperty(window,'createEasyRpgPlayer',{configurable:true,
set:function(v){real=v;},
get:function(){return real&&function(cfg){return p.then(function(){return real(cfg);});};}});
})();</script>
```

重新整理。**Expected: 遊戲卡在載入不啟動；console 執行 `window.__epGate.open()` 後正常啟動。**（這驗證 emscripten 頂層 `var createEasyRpgPlayer` 賦值會走我們的 setter。）

- [ ] **Step 5: V4——二次 populate 冪等**

遊戲啟動且有存檔的狀態下，console 執行：

```js
easyrpgPlayer.FS.syncfs(true, function(err){ console.log('repopulate done', err); });
```

**Expected: 無錯誤，`window.__epSaves.read()` 檔案數量與內容大小不變，遊戲繼續正常。**

- [ ] **Step 6: 附帶檢查——自訂引擎同名工廠**

```powershell
Select-String C:\opensource\easyRPG-web\players\custom\index.js -Pattern "createEasyRpgPlayer" -List
```

**Expected: 有匹配**（自訂引擎也走同一個閘門）。

- [ ] **Step 7: 記錄結果並還原實驗**

還原 Step 4 對 dist 的手動編輯。把 V1–V4 結果寫進本計畫檔末尾「Task 1 結果」區塊，commit：

```powershell
git checkout -b feat/seamless-cloudsave
git add docs/superpowers/plans/2026-07-10-seamless-cloud-save.md
git commit -m "docs(plan): 無感存檔同步時序驗證結果"
```

**決策表（任一 FAIL 先停下回報再繼續）：**

| 驗證 | FAIL 時的替代路線 |
|---|---|
| V1（存檔→syncfs） | 即推退回 30 秒前景輪詢＋pagehide（舊法） |
| V2（讀檔選單重掃） | onSnapshot 拉回後改「寫入＋下次開頁生效」；開機閘門仍消滅開頁 reload |
| V3（工廠包裝攔截） | 放棄閘門；開機同步改為 module ready 後執行，接受極小競態，衝突交給逐槽合併 |
| V4（二次 populate） | 開機套用改在 module ready 後直接寫（接受與首次 populate 的競態），或退 spec 保底：拉完 reload 一次 |

---

### Task 2: `decideSlots` 純函式＋單元測試

**Files:**
- Create: `web/savemerge.js`
- Create: `web/package.json`
- Test: `tests/test_savemerge.mjs`

**Interfaces:**
- Produces: `decideSlots(local, cloud, last) → { pull, push, deleteLocal, deleteCloud }`（皆檔名陣列）。
  - `local`: `{ 檔名: { fp: string, mtime: number } }`（mtime＝毫秒）
  - `cloud`: `{ 檔名: { fp: string, updatedAt: number } }`（updatedAt＝毫秒）
  - `last`: `{ 檔名: fp字串 }`＝上次同步完成時兩邊一致的指紋
- Task 4 的 `savepanel.js` 以 `import { decideSlots } from './savemerge.js'` 消費。

- [ ] **Step 1: 寫 `web/package.json`**

```json
{"type":"module"}
```

（讓 node 把 `web/*.js` 當 ESM 載入；`pwa.install_web_assets` 只複製 `.js/.css/.woff2/.png`，此檔不會進 dist。）

- [ ] **Step 2: 寫失敗測試 `tests/test_savemerge.mjs`**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { decideSlots } from '../web/savemerge.js';

const EMPTY = { pull: [], push: [], deleteLocal: [], deleteCloud: [] };
const L = (fp, mtime = 0) => ({ fp, mtime });
const C = (fp, updatedAt = 0) => ({ fp, updatedAt });

test('雙方一致 → 無事', () => {
  assert.deepEqual(
    decideSlots({ a: L('x') }, { a: C('x') }, { a: 'x' }), EMPTY);
});

test('本機沒動、雲端變了 → 拉', () => {
  assert.deepEqual(
    decideSlots({ a: L('x') }, { a: C('y') }, { a: 'x' }),
    { ...EMPTY, pull: ['a'] });
});

test('本機變了、雲端沒動 → 推', () => {
  assert.deepEqual(
    decideSlots({ a: L('y') }, { a: C('x') }, { a: 'x' }),
    { ...EMPTY, push: ['a'] });
});

test('雙邊衝突 → 雲端較新則拉', () => {
  assert.deepEqual(
    decideSlots({ a: L('y', 100) }, { a: C('z', 200) }, { a: 'x' }),
    { ...EMPTY, pull: ['a'] });
});

test('雙邊衝突 → 本機較新則推', () => {
  assert.deepEqual(
    decideSlots({ a: L('y', 300) }, { a: C('z', 200) }, { a: 'x' }),
    { ...EMPTY, push: ['a'] });
});

test('本機獨有、上次沒有 → 新增推', () => {
  assert.deepEqual(
    decideSlots({ a: L('x') }, {}, {}), { ...EMPTY, push: ['a'] });
});

test('雲端獨有、上次沒有 → 新增拉', () => {
  assert.deepEqual(
    decideSlots({}, { a: C('x') }, {}), { ...EMPTY, pull: ['a'] });
});

test('本機刪了、雲端沒動 → 刪雲端', () => {
  assert.deepEqual(
    decideSlots({}, { a: C('x') }, { a: 'x' }),
    { ...EMPTY, deleteCloud: ['a'] });
});

test('雲端刪了、本機沒動 → 刪本機', () => {
  assert.deepEqual(
    decideSlots({ a: L('x') }, {}, { a: 'x' }),
    { ...EMPTY, deleteLocal: ['a'] });
});

test('雲端刪了但本機又改過 → 改動勝，推', () => {
  assert.deepEqual(
    decideSlots({ a: L('y') }, {}, { a: 'x' }),
    { ...EMPTY, push: ['a'] });
});

test('本機刪了但雲端又改過 → 改動勝，拉', () => {
  assert.deepEqual(
    decideSlots({}, { a: C('y') }, { a: 'x' }),
    { ...EMPTY, pull: ['a'] });
});

test('兩邊皆無、只剩 last 殘留 → 無事', () => {
  assert.deepEqual(decideSlots({}, {}, { a: 'x' }), EMPTY);
});
```

- [ ] **Step 3: 跑測試確認失敗**

Run: `node --test tests/test_savemerge.mjs`
Expected: FAIL（`Cannot find module ... web/savemerge.js`）

- [ ] **Step 4: 寫 `web/savemerge.js`**

```js
// 逐槽三方合併決策（純函式、零相依；瀏覽器與 node --test 共用）。
// local: { 檔名: {fp, mtime} }（mtime＝毫秒）
// cloud: { 檔名: {fp, updatedAt} }（updatedAt＝毫秒）
// last:  { 檔名: fp }＝上次同步完成時兩邊一致的指紋
// 回傳 { pull, push, deleteLocal, deleteCloud }（皆為檔名陣列）。
// spec: docs/superpowers/specs/2026-07-10-seamless-cloud-save-design.md 合併表
export function decideSlots(local, cloud, last) {
  const out = { pull: [], push: [], deleteLocal: [], deleteCloud: [] };
  const names = new Set([
    ...Object.keys(local), ...Object.keys(cloud), ...Object.keys(last),
  ]);
  for (const n of names) {
    const l = local[n]; const c = cloud[n]; const s = last[n];
    if (l && c) {
      if (l.fp === c.fp) continue;                                  // 已一致
      if (l.fp === s) out.pull.push(n);                             // 本機沒動 → 雲端勝
      else if (c.fp === s) out.push.push(n);                        // 雲端沒動 → 本機勝
      else (c.updatedAt > l.mtime ? out.pull : out.push).push(n);   // 雙邊衝突 → 較新者勝
    } else if (l) {
      // 雲端缺席：上次也沒有＝本機新增；上次有但本機又改＝改動勝；否則雲端刪除傳播
      if (s === undefined || l.fp !== s) out.push.push(n);
      else out.deleteLocal.push(n);
    } else if (c) {
      if (s === undefined || c.fp !== s) out.pull.push(n);
      else out.deleteCloud.push(n);
    }
    // 兩邊皆無、只剩 last 殘留 → 無事，下次寫同步點時自然清掉
  }
  return out;
}
```

- [ ] **Step 5: 跑測試確認通過**

Run: `node --test tests/test_savemerge.mjs`
Expected: 12 pass, 0 fail

- [ ] **Step 6: Commit**

```powershell
git add web/savemerge.js web/package.json tests/test_savemerge.mjs
git commit -m "feat(web): 逐槽三方合併決策 decideSlots（純函式＋node 測試）"
```

---

### Task 3: `pwa.py`——`_SAVE_UI` 重構＋開機閘門

**Files:**
- Modify: `pwa.py`（`_SAVE_UI`＝213–334 附近；`write_game_pages` 的 `new_head`＝537 附近）
- Test: `tests/test_pwa_gamepages.py`

**Interfaces:**
- Consumes: 無（自足）。
- Produces（Task 4 的 `savepanel.js` 依賴這些）：
  - `window.__epSaves = { ready():bool, fs():FS|null, fp(Uint8Array):string, read():[{name,data,mtime}], write(files):Promise, remove(names):Promise }`
  - `window.__epSavePanel = { open(), close() }`（維修面板 #savepanel）
  - `window.__epGate = { done:Promise, open() }`（head 閘門；2 秒超時自動 open）
  - DOM：工具列 `#cloud-ind`（預設 hidden）、`#savepanel` 內空的 `#sp-cloud`、`#dlpanel` 含 `#dlgame`/`#saveexp`/`#saveimp`

- [ ] **Step 1: 先改測試（TDD）**

`tests/test_pwa_gamepages.py` 的 `test_write_game_pages_injects_save_ui`（25–47 行）整個換成：

```python
def test_write_game_pages_injects_save_ui(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    pwa.write_game_pages(dist, [{"label": "甲", "slug": "g", "cover_rel": None}])
    html = (dist / "play-g.html").read_text(encoding="utf-8")
    assert 'id="saveui"' in html
    # 存檔鈕已消滅 → 換成預設隱藏的狀態指示器
    assert 'id="save-open"' not in html
    assert 'id="cloud-ind"' in html and 'id="cloud-ind" hidden' in html
    # zip 導出/導入搬進「下載」面板；下載鈕改開面板
    assert 'id="dlpanel"' in html and 'id="dlgame"' in html
    assert "導出存檔" in html and "導入存檔" in html
    assert 'id="savefile"' in html
    # 維修面板（雲端同步）殼還在，內容由 savepanel.js 填
    assert 'id="savepanel"' in html and 'id="sp-cloud"' in html
    assert "__epSavePanel" in html
    # 非全螢幕才顯示（fullscreenchange 控制）
    assert "fullscreenchange" in html and "fullscreenElement" in html
    # 存檔資料夾＝/easyrpg/<game>/Save（找不到再走訪 FS）；zip 邏輯保留
    assert "/easyrpg/" in html and "/Save" in html
    assert "walkDir" in html and "saveDir" in html
    assert "makeZip" in html and "syncfs" in html
    assert 'SLUG="g"' in html or 'SLUG = "g"' in html
    # __epSaves 介面（含新增的 fp/ready/fs/remove 與 read 的 mtime）
    assert "window.__epSaves" in html
    assert "fp:function" in html and "remove:function" in html
    assert "mtime" in html
    # 開機閘門在 <head>
    assert "__epGate" in html
    assert html.index("__epGate") < html.index("</head>")
    # 攻略/留言在收藏鈕之後（原以 save-open 為錨，改用 fav-btn）
    assert html.index('id="wt-open"') > html.index('id="fav-btn"')
    assert html.index('id="cm-open"') > html.index('id="wt-open"')
```

- [ ] **Step 2: 跑測試確認失敗**

Run: `python -m pytest tests/test_pwa_gamepages.py::test_write_game_pages_injects_save_ui -q`
Expected: FAIL（`id="save-open"` 仍存在、`cloud-ind` 不存在）

- [ ] **Step 3: 改 `_SAVE_UI` 的 HTML 骨架**

`pwa.py` `_SAVE_UI` 內：

(a) 工具列那行，`<button id="save-open">存檔</button>` 換成 `<button id="cloud-ind" hidden>☁</button>`：

```html
<div id="saveui"><button id="cloud-ind" hidden>☁</button><button id="fav-btn" title="收藏">♡</button><span id="pt-label" ...></span><button id="wt-open">攻略</button><button id="cm-open">留言</button><button id="share-btn">分享</button><button id="dl-zip">下載</button>
<input id="savefile" type="file" accept=".zip" style="display:none"></div>
```

(b) `#savepanel` 區塊（235–240 行）換成兩個面板：

```html
<div id="savepanel" hidden><div class="sp-bd"></div><div class="sp-dlg">
<button class="sp-close" type="button">✕</button><h3>雲端同步</h3>
<div id="sp-cloud"></div>
</div></div>
<div id="dlpanel" hidden><div class="sp-bd"></div><div class="sp-dlg">
<button class="sp-close" type="button">✕</button><h3>下載</h3>
<button id="dlgame" class="sp-btn" type="button">下載遊戲（供離線遊玩）</button>
<button id="saveexp" class="sp-btn" type="button">導出存檔（下載 zip）</button>
<button id="saveimp" class="sp-btn" type="button">導入存檔（上傳 zip）</button>
</div></div>
```

(c) `<style>` 裡所有 `#savepanel` 開頭的選擇器補上 `#dlpanel` 對應（例：`#savepanel,#dlpanel{position:fixed;...}`、`#savepanel .sp-dlg,#dlpanel .sp-dlg{...}`……每一條都成對）。

- [ ] **Step 4: 改 `_SAVE_UI` 的 JS**

(a) `block()` 的白名單加 `#dlpanel`：

```js
if(t&&t.closest&&(t.closest("#wt-panel")||t.closest("#cm-panel")||t.closest("#savepanel")||t.closest("#dlpanel")||t.closest("#saveui")))return;
```

(b) `readSaves()` 補 mtime（FS.stat 回傳的 mtime 是 Date，`+` 轉毫秒）：

```js
function readSaves(){var FS=mod().FS,dir=saveDir(FS,false),out=[];if(!dir)return out;
FS.readdir(dir).forEach(function(n){if(n==="."||n==="..")return;try{if(isDir(FS,dir+"/"+n))return;
var d=FS.readFile(dir+"/"+n);if(d&&d.length)out.push({name:n,data:d,mtime:+FS.stat(dir+"/"+n).mtime});}catch(e){}});return out;}
```

(c) `window.__epSaves` 擴充：

```js
window.__epSaves={
ready:function(){return !!mod();},
fs:function(){var m=mod();return m?m.FS:null;},
fp:function(d){return crc32(d).toString(16)+":"+d.length;},
read:function(){return mod()?readSaves():[];},
write:function(files){return new Promise(function(res,rej){var m=mod();if(!m){rej(new Error("遊戲尚未載入"));return;}
try{var FS=m.FS,dir=saveDir(FS,true)||guessDir();mkdirp(FS,dir);
files.forEach(function(fl){FS.writeFile(dir+"/"+fl.name,fl.data);});
FS.syncfs(false,function(){res();});}catch(e){rej(e);}});},
remove:function(names){return new Promise(function(res,rej){var m=mod();if(!m){rej(new Error("遊戲尚未載入"));return;}
try{var FS=m.FS,dir=saveDir(FS,false);
if(dir)names.forEach(function(n){try{FS.unlink(dir+"/"+n);}catch(e){}});
FS.syncfs(false,function(){res();});}catch(e){rej(e);}});}};
```

(d) 面板開關通用化，取代原本 `save-open`/`spClose` 那段（298–301 行）：

```js
function wirePanel(id,key){var p=document.getElementById(id);
function close(){p.hidden=true;window.__epPause(false,key);}
p.querySelector(".sp-close").onclick=close;p.querySelector(".sp-bd").onclick=close;
return {open:function(){p.hidden=false;window.__epPause(true,key);},close:close};}
window.__epSavePanel=wirePanel("savepanel","save");
var dlPanel=wirePanel("dlpanel","dl");
```

（原 `document.getElementById("save-open").onclick=...` 刪除。）

(e) 下載鈕改開面板；原整包下載邏輯掛到 `#dlgame`（原 `document.getElementById("dl-zip").onclick=function(){...}` 長函式只改掛載目標與開頭）：

```js
document.getElementById("dl-zip").onclick=function(){dlPanel.open();};
document.getElementById("dlgame").onclick=function(){var btn=this;if(btn.disabled)return;...（原 dl-zip 函式主體原樣搬過來）...};
```

（`#saveexp`/`#saveimp` 的既有 handler 不用動——元素只是搬進 `#dlpanel`，id 不變。）

- [ ] **Step 5: 加 `_GATE_SNIPPET` 並注入 `<head>`**

`pwa.py` 模組層（`_SAVE_UI` 之後）新增：

```python
# 開機閘門：包住 emscripten MODULARIZE 工廠 createEasyRpgPlayer，讓引擎啟動先等
# 雲端 manifest（savepanel.js 讀完後 __epGate.open()）。2 秒超時 fail-open——
# 雲端有任何問題（未登入/離線/savepanel 沒載入）都不能擋玩遊戲。
# 原理：頂層 var 賦值會觸發我們預先 defineProperty 的 setter，取用時回傳包了
# gate promise 的 wrapper；外殼在 window load 才呼叫，屆時 index.js（async）必已就位。
_GATE_SNIPPET = (
    "\n<script>(function(){var open,p=new Promise(function(r){open=r;});"
    "var t=setTimeout(open,2000);"
    "window.__epGate={done:p,open:function(){clearTimeout(t);open();}};"
    "var real=null;"
    "Object.defineProperty(window,'createEasyRpgPlayer',{configurable:true,"
    "set:function(v){real=v;},"
    "get:function(){return real&&function(cfg){return p.then(function(){return real(cfg);});};}"
    "});})();</script>"
)
```

`write_game_pages` 的 `new_head`（537 行起）開頭加上它：

```python
        new_head = (
            _GATE_SNIPPET +
            canvas_fix +
            touch_style +
            ...（其餘不動）
```

- [ ] **Step 6: 跑測試**

Run: `python -m pytest tests/test_pwa_gamepages.py tests/test_pwa_touch_layout.py -q`
Expected: 全 PASS（touch_layout 用 `apad-enter` 錨點，不受影響）

- [ ] **Step 7: 跑全套建置測試**

Run: `python -m pytest tests/ -q`
Expected: PASS（若其他測試斷言了 `save-open`，一併修正該斷言）

- [ ] **Step 8: Commit**

```powershell
git add pwa.py tests/test_pwa_gamepages.py
git commit -m "feat(pwa): 存檔鈕改狀態指示器＋zip 進下載面板＋開機閘門 _GATE_SNIPPET"
```

---

### Task 4: `web/savepanel.js` 整檔重寫——同步引擎

**Files:**
- Rewrite: `web/savepanel.js`（整檔覆蓋；現有未 commit 的舊自動同步依定案不保留）

**Interfaces:**
- Consumes: Task 2 的 `decideSlots`；Task 3 的 `__epSaves`/`__epSavePanel`/`__epGate`/`#cloud-ind`/`#sp-cloud`；`web/account.js` 的 `db, isReady, currentUser, onAuthChange, signInWithGoogle, signOutUser`。
- Produces: 無對外介面（自足模組）。

- [ ] **Step 1: 整檔寫入以下內容**

```js
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
    for (const n of m.names) out[n] = { fp: ' legacy', updatedAt: base };
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
```

- [ ] **Step 2: 語法檢查**

Run: `node --check web/savepanel.js`
Expected: 無輸出（exit 0）

- [ ] **Step 3: 跑既有測試確認沒破壞建置端**

Run: `python -m pytest tests/ -q; node --test tests/test_savemerge.mjs`
Expected: 全 PASS

- [ ] **Step 4: Commit**

```powershell
git add web/savepanel.js
git commit -m "feat(web): savepanel.js 重寫——逐槽自動同步引擎（開機閘門＋即推＋即拉＋維修面板）"
```

---

### Task 5: 重建 dist、冒煙與雙裝置 E2E

**Files:** 無新程式碼；產出＝驗證通過的 dist 與（若冒煙發現 bug 的）修正 commit。

**Interfaces:**
- Consumes: Task 2–4 全部。

- [ ] **Step 1: 把新 web 資產與遊戲頁刷進 dist**

JS/CSS 快速刷新：

```powershell
python -c "import pwa; print(pwa.install_web_assets('dist'))"
```

遊戲頁 HTML（含 `_SAVE_UI`/`_GATE_SNIPPET`）需重生成：用 GUI（`python easyrpg_web_gui.py`）對現有專案執行重建。Expected: `dist/play-*.html` 內含 `cloud-ind` 與 `__epGate`。

- [ ] **Step 2: 單機冒煙**

`python -m http.server 8000 --directory dist`，開一款遊戲：

1. 未登入：工具列出現「☁ 同步」，沒有「存檔」鈕；遊戲正常開（閘門立即放行）。
2. 「下載」開面板：三顆鈕都在，導出存檔可下載 zip。
3. 點「☁ 同步」→ Google 登入 → 按鈕消失。
4. 遊戲內存檔 → 3 秒後 DevTools Network 見 Firestore 批次寫入；Firestore console 見 `slots` 新格式 manifest。
5. 重新整理頁面 → 開機閘門：Network 先見 manifest 讀取、引擎才啟動；不觸發 reload。

- [ ] **Step 3: 雙裝置 E2E（兩個瀏覽器 profile、同帳號、同遊戲）**

1. A 存槽 1 → B 不重整，開遊戲內讀檔選單 → 秒級內見槽 1 新進度。
2. A 存槽 1、B 存槽 2（都離線前先確認同步完成）→ 兩邊最終都有槽 1＋槽 2（逐槽合併，無對話框）。
3. 兩邊同槽都改 → 較新一邊的內容勝出，全程無對話框。
4. B 登出 → 「☁ 同步」重現；本機存檔不動。
5. 舊資料相容：對只有舊格式（`names`，無 `slots`）manifest 的遊戲同步一次 → manifest 被改寫成 `slots` 格式，存檔內容正確。

- [ ] **Step 4: 記錄結果並收尾**

E2E 結果寫進本檔末尾「Task 5 結果」。

```powershell
git add docs/superpowers/plans/2026-07-10-seamless-cloud-save.md
git commit -m "docs(plan): 無感存檔同步 E2E 驗證結果"
```

（合併回 main 前照例跑 superpowers:finishing-a-development-branch；push 前依專案慣例驗證無金鑰。）

---

## Task 1 結果

（執行後填寫：V1 / V2 / V3 / V4 / 自訂引擎檢查 各 PASS/FAIL 與備註）

## Task 5 結果

（執行後填寫）
