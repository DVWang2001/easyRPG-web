import io
import json
import tarfile
from pathlib import Path

import easyrpg_web_build as core


def _fake_player_tarball(path: Path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in [
            ("index.html", b"<html><head><title>EasyRPG Player</title></head><body><script>createEasyRpgPlayer({ game: undefined, saveFs: undefined });</script></body></html>"),
            ("index.js", b"// js"),
            ("index.wasm", b"\0asm"),
        ]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    path.write_bytes(buf.getvalue())


def _game(root: Path, marker: str):
    root.mkdir()
    (root / "RPG_RT.ldb").write_text(marker)


def test_build_library_two_games(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    g1 = tmp_path / "Hanayome"
    _game(g1, "1")
    g2 = tmp_path / "Brave"
    _game(g2, "2")
    out = tmp_path / "dist"

    result = core.build_library(
        games=[{"folder": g1, "label": "花嫁之冠", "cover": None},
               {"folder": g2, "label": "勇者傳說", "cover": None}],
        app_label="我的遊戲庫", app_icon=None, soundfont=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )

    assert result == out
    assert (out / "play.html").exists()
    assert not (out / "index.html").read_text(encoding="utf-8").startswith("<html><head></head>")
    play = (out / "play.html").read_text(encoding="utf-8")
    assert "serviceWorker" in play
    grid = (out / "index.html").read_text(encoding="utf-8")
    assert "我的遊戲庫" in grid
    assert grid.count('class="card"') == 2
    assert "花嫁之冠" in grid
    assert "勇者傳說" in grid
    assert 'href="play-game.html"' in grid
    assert 'href="play-game-2.html"' in grid
    assert (out / "play-game.html").exists()
    assert (out / "play-game-2.html").exists()
    assert (out / "games" / "game" / "index.json").exists()
    assert (out / "games" / "game-2" / "index.json").exists()
    manifest = json.loads((out / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["start_url"] == "."
    sw = (out / "service-worker.js").read_text(encoding="utf-8")
    assert "play.html" in sw
    assert "games/game/index.json" in sw


def test_build_library_empty_rejected(tmp_path):
    try:
        core.build_library(games=[], out=tmp_path / "dist")
        assert False, "空清單應報錯"
    except core.BuildError:
        pass


def test_build_library_names_invalid_game(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    good = tmp_path / "Good"
    _game(good, "1")
    bad = tmp_path / "Bad"
    bad.mkdir()
    (bad / "readme.txt").write_text("nope")
    out = tmp_path / "dist"

    try:
        core.build_library(
            games=[{"folder": good, "label": "好遊戲", "cover": None},
                   {"folder": bad, "label": "壞遊戲", "cover": None}],
            app_icon=None, soundfont=None, out=out,
            player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
        )
        assert False, "非法遊戲應中止"
    except core.BuildError as e:
        assert "壞遊戲" in str(e)


def test_build_library_assigns_unique_slugs(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    g1 = tmp_path / "A"
    _game(g1, "1")
    g2 = tmp_path / "B"
    _game(g2, "2")
    out = tmp_path / "dist"

    core.build_library(
        games=[{"folder": g1, "label": "Dungeon", "cover": None},
               {"folder": g2, "label": "Dungeon", "cover": None}],
        app_icon=None, soundfont=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )
    assert (out / "games" / "dungeon" / "index.json").exists()
    assert (out / "games" / "dungeon-2" / "index.json").exists()


def test_build_library_passes_rtp_through(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    g1 = tmp_path / "Game"
    _game(g1, "1")
    rtp = tmp_path / "rtp"
    rtp.mkdir()
    (rtp / "extra.png").write_text("rtp-asset")
    out = tmp_path / "dist"

    core.build_library(
        games=[{"folder": g1, "label": "遊戲", "cover": None, "rtp": rtp}],
        app_icon=None, soundfont=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )

    # label「遊戲」是 CJK → slug 退回 ASCII "game"
    assert (out / "games" / "game" / "extra.png").read_text() == "rtp-asset"


def test_build_library_per_game_page(tmp_path):
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    g1 = tmp_path / "Hanayome"
    _game(g1, "1")
    cover = tmp_path / "c.png"
    cover.write_bytes(b"\x89PNG")
    out = tmp_path / "dist"

    core.build_library(
        games=[{"folder": g1, "label": "花嫁之冠", "cover": cover}],
        app_icon=None, soundfont=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )

    page = (out / "play-game.html").read_text(encoding="utf-8")  # 花嫁之冠 → slug "game"
    assert "<title>花嫁之冠</title>" in page
    assert '<link rel="icon" href="games/game/cover.png">' in page
    assert 'game: "game"' in page
