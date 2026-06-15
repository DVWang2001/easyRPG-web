import io
import json
import tarfile
from pathlib import Path

import easyrpg_web_build as core


def _fake_player_tarball(path: Path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in [
            ("index.html", b"<html><head></head><body></body></html>"),
            ("index.js", b"// js"),
            ("index.wasm", b"\0asm"),
        ]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    path.write_bytes(buf.getvalue())


def _make_game(root: Path):
    root.mkdir()
    (root / "RPG_RT.ldb").write_text("x")
    (root / "RPG_RT.lmt").write_text("x")
    cs = root / "CharSet"
    cs.mkdir()
    (cs / "Hero.png").write_bytes(b"png")


def test_build_produces_self_contained_dist(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    game = tmp_path / "MyGame"
    _make_game(game)
    sf = tmp_path / "win.sf2"
    sf.write_bytes(b"RIFFsfbk")
    icon = tmp_path / "icon.png"
    icon.write_bytes(b"\x89PNG")
    out = tmp_path / "dist"

    result = core.build(
        game=game, app_label="花嫁之冠", soundfont=sf, app_icon=icon,
        out=out, player_cache=tmp_path / "cache",
        player_url=tarball.resolve().as_uri(),
    )

    assert result == out
    assert (out / "index.wasm").exists()
    assert (out / "games" / "default" / "RPG_RT.ldb").exists()
    assert (out / "games" / "default" / "easyrpg.soundfont").exists()
    idx = json.loads((out / "games" / "default" / "index.json").read_text(encoding="utf-8"))
    assert idx["metadata"]["version"] == 2
    assert idx["cache"]["rpg_rt.ldb"] == "RPG_RT.ldb"
    assert (out / "manifest.webmanifest").exists()
    assert (out / "service-worker.js").exists()
    assert (out / "icons" / "icon.png").exists()
    assert 'rel="manifest"' in (out / "index.html").read_text(encoding="utf-8")


def test_app_label_defaults_to_game_folder_name(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    game = tmp_path / "勇者傳說"
    _make_game(game)
    out = tmp_path / "dist"

    core.build(
        game=game, soundfont=None, app_icon=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )

    manifest = json.loads((out / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["name"] == "勇者傳說"


def test_build_rejects_non_rpgmaker_folder(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    game = tmp_path / "NotAGame"
    game.mkdir()
    (game / "readme.txt").write_text("nope")
    out = tmp_path / "dist"

    try:
        core.build(
            game=game, out=out, player_cache=tmp_path / "cache",
            player_url=tarball.resolve().as_uri(),
        )
        assert False, "應該因缺 RPG_RT.* 而報錯"
    except core.BuildError:
        pass
