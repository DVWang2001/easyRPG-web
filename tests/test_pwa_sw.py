from pathlib import Path

import pwa


def test_service_worker_cache_first_runtime(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    out = pwa.write_service_worker(dist)

    assert out == dist / "service-worker.js"
    text = out.read_text(encoding="utf-8")
    # 單一 runtime 快取，不預載整個庫
    assert "easyrpg-games" in text
    assert "addEventListener('install'" in text
    assert "addEventListener('fetch'" in text
    # cache-first + runtime 快取（c.put）
    assert "caches.match(e.request)" in text
    assert "c.put(e.request" in text
    # 導航才退回殼頁，素材回傳錯誤
    assert "navigate" in text
    assert "Response.error()" in text
