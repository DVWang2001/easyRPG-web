import io
import tarfile
from pathlib import Path

import pytest

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


def _write_player_files(d: Path):
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text("<html></html>")
    (d / "index.js").write_text("// js")
    (d / "index.wasm").write_bytes(b"\0asm")


def test_ensure_player_variant_custom_returns_bundled(tmp_path, monkeypatch):
    custom = tmp_path / "custom"
    _write_player_files(custom)
    monkeypatch.setitem(player_fetch.BUNDLED, "custom", custom)
    # variant=custom 直接用本機自訂版，不下載（給一個會壞的 url 確保沒被用到）
    out = player_fetch.ensure_player(tmp_path / "cache", url="http://0.0.0.0/none",
                                     variant="custom")
    assert out == custom
    assert (out / "index.wasm").exists()


def test_ensure_player_variant_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setitem(player_fetch.BUNDLED, "custom", tmp_path / "nope")
    with pytest.raises(FileNotFoundError):
        player_fetch.ensure_player(tmp_path / "cache", variant="custom")


def test_ensure_player_variant_official_uses_backup(tmp_path, monkeypatch):
    official = tmp_path / "official"
    _write_player_files(official)
    monkeypatch.setitem(player_fetch.BUNDLED, "official", official)
    out = player_fetch.ensure_player(tmp_path / "cache", url="http://0.0.0.0/none",
                                     variant="official")
    assert out == official


def test_ensure_player_auto_still_downloads(tmp_path):
    tarball = tmp_path / "fake.tar.gz"
    _make_fake_player_tarball(tarball)
    out = player_fetch.ensure_player(tmp_path / "cache", url=tarball.resolve().as_uri(),
                                     variant="auto")
    assert (out / "index.wasm").exists()
