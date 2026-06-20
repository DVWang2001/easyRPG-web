from pathlib import Path

import pwa


def test_service_worker_network_first_shell_cache_first_games(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    out = pwa.write_service_worker(dist)

    assert out == dist / "service-worker.js"
    text = out.read_text(encoding="utf-8")

    # 仍用單一快取，離線下載的遊戲資料保留
    assert "easyrpg-games" in text
    assert "addEventListener('install'" in text
    assert "skipWaiting" in text
    assert "addEventListener('fetch'" in text

    # 用路徑區分「遊戲大檔」與「外殼」
    assert "isGameAsset" in text
    assert "/games/" in text

    # 外殼 network-first，且用 no-cache 繞過 HTTP 快取（部署後才看得到更新）
    assert "fetch(e.request, { cache: 'no-cache' }).then" in text
    # 遊戲資料 cache-first：快取優先 + runtime put
    assert "caches.match(e.request)" in text
    assert "c.put(e.request" in text

    # 離線：導航退回殼頁、素材回錯誤
    assert "caches.match('index.html')" in text
    assert "Response.error()" in text


def test_service_worker_build_stamp_changes_each_deploy(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    a = pwa.write_service_worker(dist, build="20260101000000").read_text(encoding="utf-8")
    assert "const BUILD = '20260101000000'" in a
    assert "__BUILD__" not in a                       # 佔位符已替換
    b = pwa.write_service_worker(dist, build="20260102000000").read_text(encoding="utf-8")
    assert a != b                                     # 不同部署→SW 內容不同→瀏覽器更新
