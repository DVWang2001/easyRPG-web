import json
from pathlib import Path

import pwa


def test_install_icon_copies_and_returns_rel(tmp_path):
    icon = tmp_path / "src.png"
    icon.write_bytes(b"\x89PNG")
    dist = tmp_path / "dist"
    dist.mkdir()

    rel = pwa.install_icon(dist, icon)

    assert rel == "icons/icon.png"
    assert (dist / "icons" / "icon.png").read_bytes() == b"\x89PNG"


def test_write_manifest_contents(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()

    out = pwa.write_manifest(dist, "花嫁之冠", "icons/icon.png")

    assert out == dist / "manifest.webmanifest"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["name"] == "花嫁之冠"
    assert data["display"] == "standalone"
    assert data["start_url"] == "."
    assert any(i["src"] == "icons/icon.png" for i in data["icons"])
