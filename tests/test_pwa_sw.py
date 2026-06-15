import re
from pathlib import Path

import pwa


def test_service_worker_precaches_all_dist_files(tmp_path):
    dist = tmp_path / "dist"
    (dist / "games" / "default").mkdir(parents=True)
    (dist / "index.wasm").write_bytes(b"\0asm")
    (dist / "games" / "default" / "RPG_RT.ldb").write_text("x")

    out = pwa.write_service_worker(dist)

    assert out == dist / "service-worker.js"
    text = out.read_text(encoding="utf-8")
    assert "index.wasm" in text
    assert "games/default/RPG_RT.ldb" in text
    assert "service-worker.js" not in re.search(r"PRECACHE\s*=\s*\[(.*?)\]", text, re.S).group(1)


def test_service_worker_has_install_and_fetch_handlers(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("x")
    text = pwa.write_service_worker(dist).read_text(encoding="utf-8")
    assert "addEventListener('install'" in text
    assert "addEventListener('fetch'" in text
