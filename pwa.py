"""PWA 外殼：圖示、manifest、service worker、改寫 index.html。"""
from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path

ICON_REL = "icons/icon.png"
WEB_DIR = Path(__file__).resolve().parent / "web"


def install_icon(dist, icon_path) -> str:
    dist = Path(dist)
    target = dist / ICON_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(icon_path), target)
    return ICON_REL


def _build_manifest(
    name: str, start_url: str, icon_rel: str, scope: str = ".", app_id: str | None = None
) -> dict:
    return {
        "name": name,
        "short_name": name,
        # id 決定 Android Chrome 眼中的 App 身分；預設＝start_url（與 Chrome 自動推算一致、且穩定）。
        "id": app_id or start_url,
        "start_url": start_url,
        # scope 決定 App「範圍」；每遊戲收窄到自己的頁，避免裝了一個就被視為已涵蓋其他遊戲。
        "scope": scope,
        "display": "standalone",
        "orientation": "landscape",
        "background_color": "#000000",
        "theme_color": "#000000",
        "icons": [
            {"src": icon_rel, "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": icon_rel, "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": icon_rel, "sizes": "180x180", "type": "image/png"},
        ],
    }


def write_manifest(dist, app_label: str, icon_rel: str = ICON_REL) -> Path:
    dist = Path(dist)
    out = dist / "manifest.webmanifest"
    out.write_text(
        json.dumps(_build_manifest(app_label, ".", icon_rel), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return out


SW_TEMPLATE = """\
// 由 easyrpg_web_build 產生：
//   遊戲大檔（games/ 底下）→ cache-first（離線下載保留，幾乎不變）。
//   外殼（HTML/JS/WASM/manifest 等）→ network-first（線上永遠拿最新 → 部署即生效；離線退回快取）。
// 「下載某個遊戲以供離線」由各遊戲頁自己處理（見 precache-<slug>.json），快取進 easyrpg-games。
const CACHE = 'easyrpg-games';
// 每次部署都會變（時間戳）→ service-worker.js 內容改變 → 瀏覽器偵測到新版 SW 並更新。
const BUILD = '__BUILD__';

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      // 清掉舊版（含早期 easyrpg-web-v* 全庫快取），只保留 easyrpg-games
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

// 路徑含 /games/ 視為遊戲大檔（cache-first）；其餘為外殼（network-first）。
function isGameAsset(req) {
  try { return new URL(req.url).pathname.includes('/games/'); }
  catch (err) { return false; }
}

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  if (isGameAsset(e.request)) {
    // 遊戲資料：cache-first（離線下載優先用快取，沒有才抓網路並快取）
    e.respondWith(
      caches.match(e.request).then((hit) => {
        if (hit) return hit;
        return fetch(e.request).then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
          return res;
        });
      })
    );
  } else {
    // 外殼：network-first，且 fetch 用 no-cache 強制向伺服器重新驗證
    // （否則瀏覽器 HTTP 快取會讓「network」其實拿到舊檔，部署後看不到更新）。
    e.respondWith(
      fetch(e.request, { cache: 'no-cache' }).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
        return res;
      }).catch(() =>
        caches.match(e.request).then((hit) => {
          if (hit) return hit;
          if (e.request.mode === 'navigate') return caches.match('index.html');
          return Response.error();
        })
      )
    );
  }
});
"""


def write_service_worker(dist, build: str | None = None) -> Path:
    """寫 service-worker.js；每次部署用新的 build 戳記讓 SW 內容改變→瀏覽器強制更新。"""
    dist = Path(dist)
    if build is None:
        build = time.strftime("%Y%m%d%H%M%S")
    out = dist / "service-worker.js"
    out.write_text(SW_TEMPLATE.replace("__BUILD__", build), encoding="utf-8")
    return out


def install_web_assets(dist) -> list:
    """把 web/ 下的前端資產（js/css）複製進 dist；回傳複製的檔名清單。

    firebase-config.js 含站長填的設定一併複製；firestore.rules 是給 Firestore
    Console 貼的 artifact，不複製進 dist。
    """
    dist = Path(dist)
    copied = []
    if WEB_DIR.exists():
        for p in sorted(WEB_DIR.iterdir()):
            # 跳過 *.example.js 範本（金鑰範本不部署）
            if p.is_file() and p.suffix in (".js", ".css") and not p.name.endswith(".example.js"):
                shutil.copy2(p, dist / p.name)
                copied.append(p.name)
    return copied


import html as _html


def pwa_head(app_label: str, icon_rel: str) -> str:
    title = _html.escape(app_label)
    return (
        '\n<link rel="manifest" href="manifest.webmanifest">'
        f'\n<link rel="apple-touch-icon" href="{icon_rel}">'
        '\n<meta name="apple-mobile-web-app-capable" content="yes">'
        '\n<meta name="apple-mobile-web-app-status-bar-style" content="black">'
        f'\n<meta name="apple-mobile-web-app-title" content="{title}">'
        '\n<meta name="theme-color" content="#000000">'
        '\n<meta name="viewport" content="width=device-width, initial-scale=1, '
        'viewport-fit=cover, user-scalable=no">'
        '\n<script>'
        "if('serviceWorker' in navigator){"
        "window.addEventListener('load',function(){"
        "navigator.serviceWorker.register('service-worker.js');});}"
        '</script>\n'
    )


def patch_index_html(dist, app_label: str, icon_rel: str = ICON_REL) -> Path:
    dist = Path(dist)
    index = dist / "index.html"
    html = index.read_text(encoding="utf-8")
    snippet = pwa_head(app_label, icon_rel)
    if "</head>" in html:
        html = html.replace("</head>", snippet + "</head>", 1)
    elif "</body>" in html:
        html = html.replace("</body>", snippet + "</body>", 1)
    else:
        html = html + snippet
    index.write_text(html, encoding="utf-8")
    return index



# 遊戲頁左上角「導出/導入存檔」面板（非全螢幕時顯示）。
# 直接讀寫 EasyRPG 的存檔資料夾（emscripten FS，IDBFS 持久化），整包成 store-only zip。
# 存檔位置＝/easyrpg/<game>/Save（EasyRPG chdir 進 /easyrpg/<game> 後 --save-path Save）；
# 路徑萬一不符就走訪整個 FS 找含 SaveNN.lsd 的資料夾。__SLUG__ 替換成 JSON 字串字面值。
_SAVE_UI = r"""
<style>#saveui{position:fixed;left:8px;top:calc(8px + env(safe-area-inset-top));
z-index:10000;display:flex;gap:6px}
#saveui button{padding:5px 10px;border-radius:8px;border:1px solid #3a3a3a;
background:rgba(31,41,55,.85);color:#cbd5e1;font:12px -apple-system,sans-serif;cursor:pointer}
#saveui button:active{background:#2563eb;color:#fff}</style>
<div id="saveui"><button id="wt-open">攻略</button><button id="saveexp">導出存檔</button><button id="saveimp">導入存檔</button>
<input id="savefile" type="file" accept=".zip" style="display:none"></div>
<script>(function(){
var SLUG=__SLUG__;
// 假暫停：不停主迴圈（停了會讓 WebGL 畫布變黑且不回來），改成靜音音訊＋擋遊戲鍵盤。
// 音訊在播放器內部的 SDL audioContext，頁面拿不到 → 在遊戲建立前包裹 AudioContext 建構子攔截實例。
window.__epPause=window.__epPause||(function(){var keys={},n=0,ctxs=window.__epAudioCtxs=window.__epAudioCtxs||[];
["AudioContext","webkitAudioContext"].forEach(function(nm){var C=window[nm];if(C&&!C.__epW){var W=function(o){var c=new C(o);ctxs.push(c);return c;};W.prototype=C.prototype;W.__epW=1;try{window[nm]=W;}catch(e){}}});
function mute(on){ctxs.forEach(function(c){try{on?c.suspend():c.resume();}catch(e){}});}
function block(e){if(!window.__epPaused)return;var t=e.target;if(t&&t.closest&&(t.closest("#wt-panel")||t.closest("#saveui")))return;e.stopImmediatePropagation();e.preventDefault();}
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


# 攻略：Quill/DOMPurify（全域）＋ 該遊戲設定 ＋ 樣式/模組腳本。
# __SLUG__/__TITLE__ 會被替換成 JSON 字串字面值。
_WT_SNIPPET = """
<link href="https://cdn.quilljs.com/1.3.7/quill.snow.css" rel="stylesheet">
<link rel="stylesheet" href="walkthrough.css">
<script src="https://cdn.quilljs.com/1.3.7/quill.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.8/dist/purify.min.js"></script>
<script>window.__WT={slug:__SLUG__,title:__TITLE__};</script>
<script type="module" src="walkthrough.js"></script>
"""


def write_game_pages(dist, entries, icon_rel=ICON_REL) -> None:
    """以 dist/play.html 為模板，為每個遊戲產出 play-<slug>.html 與其專屬 manifest。

    每個遊戲頁：靜態 <title>＝遊戲名、<link rel=icon>/apple-touch-icon＝封面、
    自己的 <link rel=manifest>（icons＝封面、name＝遊戲名、start_url＝該頁），並 baked-in game。
    模板繼承的整庫 manifest / apple-touch-icon / app-title 會先被移除，
    讓 iOS「加入主畫面」用的是該遊戲封面（而非遊戲庫主圖示）。"""
    dist = Path(dist)
    template = (dist / "play.html").read_text(encoding="utf-8")
    for e in entries:
        slug = e["slug"]
        label = e["label"]
        # 有指定字表的遊戲載入 player-custom-<id>/ 引擎；其餘用根目錄官方引擎。
        table_id = e.get("name_table_id") or ""
        engine = ("player-custom-" + table_id + "/") if table_id else ""
        cover = e.get("cover_rel") or icon_rel
        cover_esc = _html.escape(cover, quote=True)
        title_esc = _html.escape(label, quote=True)
        manifest_name = "manifest-" + slug + ".webmanifest"
        # 每遊戲 manifest：icons＝封面、start_url＝該遊戲頁 → 加入主畫面得到該遊戲圖示/名稱。
        # scope/id 收窄到該遊戲頁，讓 Android Chrome 視各遊戲為獨立 App（否則裝一個就裝不了其他）。
        page_url = "play-" + slug + ".html"
        (dist / manifest_name).write_text(
            json.dumps(
                _build_manifest(label, page_url, cover, scope=page_url),
                ensure_ascii=False, indent=2,
            ),
            encoding="utf-8",
        )
        # 該遊戲的離線下載清單（殼 + 這個遊戲的所有檔），供遊戲頁自己下載
        game_dir = dist / "games" / slug
        game_files = (
            sorted(
                p.relative_to(dist).as_posix()
                for p in game_dir.rglob("*")
                if p.is_file()
            )
            if game_dir.exists()
            else []
        )
        shell = [engine + "index.js", engine + "index.wasm",
                 "play-" + slug + ".html", manifest_name, icon_rel]
        (dist / ("precache-" + slug + ".json")).write_text(
            json.dumps(shell + game_files, ensure_ascii=False), encoding="utf-8"
        )
        # 鎖住 document.title 用的 JS 字串字面值（防 </script> 注入）
        title_js = json.dumps(label).replace("<", "\\u003c")
        tmpl = (template.replace('src="index.js"', 'src="' + engine + 'index.js"')
                if engine else template)
        html = tmpl.replace("game: undefined", "game: " + json.dumps(slug))
        # 移除模板繼承的整庫 tag，避免 iOS 採用庫圖示
        html = re.sub(r'<link[^>]*rel="manifest"[^>]*>', "", html, count=1, flags=re.S)
        html = re.sub(r'<link[^>]*rel="apple-touch-icon"[^>]*>', "", html, count=1, flags=re.S)
        html = re.sub(r'<meta[^>]*name="apple-mobile-web-app-title"[^>]*>', "", html, count=1, flags=re.S)
        html = re.sub(r"<title>.*?</title>", "", html, count=1, flags=re.S)
        # 自訂(SDL3)引擎會把 canvas 內聯尺寸設成遊戲解析度(很小);用 !important 強制撐滿
        # (官方 SDL2 shell 沒這段 → SDL3 在此 shell 下會「畫面小、黑邊大」)。
        canvas_fix = ("\n<style>#canvas{width:100vw !important;height:100vh !important}</style>"
                      if engine else "")
        new_head = (
            canvas_fix +
            "\n<title>" + title_esc + "</title>"
            '\n<meta name="apple-mobile-web-app-title" content="' + title_esc + '">'
            '\n<link rel="icon" href="' + cover_esc + '">'
            '\n<link rel="apple-touch-icon" href="' + cover_esc + '">'
            '\n<link rel="manifest" href="' + manifest_name + '">'
            # 鎖標題：EasyRPG 引擎載入後會把 document.title 改成遊戲內建標題（可能是 untitled），
            # 這裡把 title 鎖成導入的名稱，讓 iOS「加入主畫面」讀到正確名稱。
            "\n<script>(function(){var t=" + title_js + ";"
            "try{Object.defineProperty(document,'title',{configurable:true,"
            "get:function(){return t;},set:function(){}});}catch(e){}"
            "document.title=t;"
            "if(window.MutationObserver){var el=document.querySelector('title');"
            "if(el){new MutationObserver(function(){if(document.title!==t){document.title=t;}})"
            ".observe(el,{childList:true,characterData:true,subtree:true});}}})();</script>\n"
        )
        html = html.replace("</head>", new_head + "</head>", 1)
        # 只下載這一個遊戲的進度條：載入時抓 precache-<slug>.json，逐檔快取進 easyrpg-games
        slug_js = json.dumps(slug)
        dl_snippet = (
            "\n<style>#dl{position:fixed;left:0;right:0;bottom:0;background:#1f2937;"
            "padding:8px 14px calc(8px + env(safe-area-inset-bottom));"
            "font:13px -apple-system,sans-serif;color:#cbd5e1;z-index:9999}"
            "#dltrack{height:5px;background:#374151;border-radius:3px;overflow:hidden}"
            "#dlbar{height:100%;width:0;background:#2563eb;transition:width .2s}"
            "#dltext{display:block;margin-top:5px}</style>"
            '\n<div id="dl" hidden><div id="dltrack"><div id="dlbar"></div></div><span id="dltext"></span></div>'
            '\n<script>(function(){if(!("caches" in window))return;var SLUG=' + slug_js + ";"
            'fetch("precache-"+SLUG+".json").then(function(r){return r.json();}).then(function(files){'
            'var box=document.getElementById("dl"),bar=document.getElementById("dlbar"),'
            'txt=document.getElementById("dltext");'
            'caches.open("easyrpg-games").then(function(cache){'
            "var total=files.length,done=0,idx=0;"
            'function show(){box.hidden=false;var pct=total?Math.round(done/total*100):100;'
            'bar.style.width=pct+"%";'
            'if(done>=total){txt.textContent="✓ 此遊戲已可離線";'
            "setTimeout(function(){box.hidden=true;},3000);}"
            'else{txt.textContent="下載此遊戲以供離線… "+pct+"% ("+done+"/"+total+")";}}'
            "show();"
            "function worker(){return (async function(){while(idx<total){var f=files[idx++];"
            "try{if(!(await cache.match(f)))await cache.add(f);}catch(e){}done++;show();}})();}"
            "var n=Math.min(6,total)||1,ws=[];for(var i=0;i<n;i++)ws.push(worker());"
            "Promise.all(ws);});}).catch(function(){});})();</script>\n"
        )
        save_snippet = _SAVE_UI.replace("__SLUG__", slug_js)
        wt_title_js = json.dumps(label).replace("<", "\\u003c")
        wt_snippet = (_WT_SNIPPET
                      .replace("__SLUG__", slug_js)
                      .replace("__TITLE__", wt_title_js))
        body_add = dl_snippet + save_snippet + wt_snippet
        if "</body>" in html:
            html = html.replace("</body>", body_add + "</body>", 1)
        else:
            html = html + body_add
        (dist / ("play-" + slug + ".html")).write_text(html, encoding="utf-8")
