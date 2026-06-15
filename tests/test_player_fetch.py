import io
import tarfile
from pathlib import Path

import player_fetch


def _make_fake_player_tarball(path: Path):
    """打包成內含 index.html/index.js/index.wasm/games 的 tar.gz。"""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in [
            ("index.html", b"<html></html>"),
            ("index.js", b"// js"),
            ("index.wasm", b"\0asm"),
            ("games/default/.keep", b""),
        ]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    path.write_bytes(buf.getvalue())


def test_ensure_player_extracts_and_returns_dir(tmp_path):
    tarball = tmp_path / "fake.tar.gz"
    _make_fake_player_tarball(tarball)
    cache = tmp_path / "cache"
    url = tarball.resolve().as_uri()

    player_dir = player_fetch.ensure_player(cache, url=url)

    assert (player_dir / "index.wasm").exists()
    assert (player_dir / "index.js").exists()
    assert (player_dir / "index.html").exists()


def test_ensure_player_uses_cache_second_time(tmp_path):
    tarball = tmp_path / "fake.tar.gz"
    _make_fake_player_tarball(tarball)
    cache = tmp_path / "cache"
    url = tarball.resolve().as_uri()

    player_fetch.ensure_player(cache, url=url)
    tarball.unlink()
    player_dir = player_fetch.ensure_player(cache, url=url)
    assert (player_dir / "index.wasm").exists()
