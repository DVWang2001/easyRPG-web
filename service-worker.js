// 由 easyrpg_web_build 產生：
//   遊戲大檔（games/ 底下）→ cache-first（離線下載保留，幾乎不變）。
//   外殼（HTML/JS/WASM/manifest 等）→ network-first（線上永遠拿最新 → 部署即生效；離線退回快取）。
// 「下載某個遊戲以供離線」由各遊戲頁自己處理（見 precache-<slug>.json），快取進 easyrpg-games。
const CACHE = 'easyrpg-games';
// 每次部署都會變（時間戳）→ service-worker.js 內容改變 → 瀏覽器偵測到新版 SW 並更新。
const BUILD = '20260701222718';

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
