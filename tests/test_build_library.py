import io
import json
import tarfile
from pathlib import Path

import easyrpg_web_build as core
import slugify


def _fake_player_tarball(path: Path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in [
            ("index.html", b'<html><head><title>EasyRPG Player</title></head><body><script async type="text/javascript" src="index.js"></script><script>createEasyRpgPlayer({ game: undefined, saveFs: undefined });</script></body></html>'),
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
    s1 = slugify.hash_slug("花嫁之冠")
    s2 = slugify.hash_slug("勇者傳說")
    assert f'href="play-{s1}.html"' in grid
    assert f'href="play-{s2}.html"' in grid
    assert (out / f"play-{s1}.html").exists()
    assert (out / f"play-{s2}.html").exists()
    assert (out / "games" / s1 / "index.json").exists()
    assert (out / "games" / s2 / "index.json").exists()
    manifest = json.loads((out / "manifest.webmanifest").read_text(encoding="utf-8"))
    assert manifest["start_url"] == "."
    # service worker：cache-first + runtime（不再預載整個庫）
    sw = (out / "service-worker.js").read_text(encoding="utf-8")
    assert "easyrpg-games" in sw
    assert "addEventListener('fetch'" in sw
    # 每遊戲離線清單各自存在
    assert (out / f"precache-{s1}.json").exists()
    assert (out / f"precache-{s2}.json").exists()


def test_build_library_per_game_custom_player(tmp_path, monkeypatch):
    import player_fetch
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    custom = tmp_path / "customengine"
    custom.mkdir()
    (custom / "index.html").write_text("<html></html>")
    (custom / "index.js").write_text("// custom js")
    (custom / "index.wasm").write_bytes(b"\0custom")
    monkeypatch.setitem(player_fetch.BUNDLED, "custom", custom)
    g1 = tmp_path / "A"
    _game(g1, "1")
    g2 = tmp_path / "B"
    _game(g2, "2")
    out = tmp_path / "dist"

    core.build_library(
        games=[{"folder": g1, "label": "自訂遊戲", "cover": None, "name_table_id": "tid1"},
               {"folder": g2, "label": "一般遊戲", "cover": None}],
        app_icon=None, soundfont=None, out=out,
        player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
    )

    s1 = slugify.hash_slug("自訂遊戲")
    s2 = slugify.hash_slug("一般遊戲")
    # 自訂引擎被放進 player-custom/
    assert (out / "player-custom" / "index.js").read_text() == "// custom js"
    assert (out / "player-custom" / "index.wasm").exists()
    # 自訂遊戲頁載入 player-custom 引擎；一般遊戲頁用根目錄引擎
    assert 'src="player-custom/index.js"' in (out / f"play-{s1}.html").read_text(encoding="utf-8")
    b = (out / f"play-{s2}.html").read_text(encoding="utf-8")
    assert 'src="index.js"' in b and "player-custom" not in b


def test_build_library_custom_player_missing_engine_errors(tmp_path, monkeypatch):
    import player_fetch
    tarball = tmp_path / "player.tar.gz"
    _fake_player_tarball(tarball)
    monkeypatch.setitem(player_fetch.BUNDLED, "custom", tmp_path / "nope")
    g1 = tmp_path / "A"
    _game(g1, "1")
    out = tmp_path / "dist"
    try:
        core.build_library(
            games=[{"folder": g1, "label": "自訂", "cover": None, "name_table_id": "tid1"}],
            app_icon=None, soundfont=None, out=out,
            player_cache=tmp_path / "cache", player_url=tarball.resolve().as_uri(),
        )
        assert False, "缺自訂引擎應報錯"
    except core.BuildError as e:
        assert "自訂播放器" in str(e)


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
    taken = set()
    d1 = slugify.hash_slug("Dungeon", taken)
    d2 = slugify.hash_slug("Dungeon", taken)
    assert (out / "games" / d1 / "index.json").exists()
    assert (out / "games" / d2 / "index.json").exists()


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

    s = slugify.hash_slug("遊戲")
    assert (out / "games" / s / "extra.png").read_text() == "rtp-asset"


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

    s = slugify.hash_slug("花嫁之冠")
    page = (out / f"play-{s}.html").read_text(encoding="utf-8")
    assert "<title>花嫁之冠</title>" in page
    assert f'<link rel="icon" href="games/{s}/cover.png">' in page
    assert f'game: "{s}"' in page
    # 每遊戲 manifest：加入主畫面用該遊戲封面/名稱、開啟即進該遊戲
    assert f'<link rel="manifest" href="manifest-{s}.webmanifest">' in page
    m = json.loads((out / f"manifest-{s}.webmanifest").read_text(encoding="utf-8"))
    assert m["name"] == "花嫁之冠"
    assert m["start_url"] == f"play-{s}.html"
    assert all(icon["src"] == f"games/{s}/cover.png" for icon in m["icons"])
