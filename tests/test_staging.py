from pathlib import Path

import staging


def _make_game(root: Path):
    (root / "RPG_RT.ldb").write_text("game")
    (root / "notes.bak").write_text("junk")
    (root / "patch.trans").write_text("junk")
    sub = root / "CharSet"
    sub.mkdir()
    (sub / "Hero.png").write_bytes(b"png")


def test_stage_copies_game_and_skips_default_ignores(tmp_path):
    game = tmp_path / "game"
    game.mkdir()
    _make_game(game)
    dest = tmp_path / "dest"

    staging.stage_game(game, dest)

    assert (dest / "RPG_RT.ldb").exists()
    assert (dest / "CharSet" / "Hero.png").exists()
    assert not (dest / "notes.bak").exists()
    assert not (dest / "patch.trans").exists()


def test_stage_injects_soundfont(tmp_path):
    game = tmp_path / "game"
    game.mkdir()
    _make_game(game)
    sf = tmp_path / "win.sf2"
    sf.write_bytes(b"RIFFsfbk")
    dest = tmp_path / "dest"

    staging.stage_game(game, dest, soundfont=sf)

    assert (dest / "easyrpg.soundfont").read_bytes() == b"RIFFsfbk"


def test_stage_rtp_then_game_overrides(tmp_path):
    rtp = tmp_path / "rtp"
    rtp.mkdir()
    (rtp / "shared.png").write_text("from-rtp")
    (rtp / "RPG_RT.ldb").write_text("rtp-version")
    game = tmp_path / "game"
    game.mkdir()
    (game / "RPG_RT.ldb").write_text("game-version")
    dest = tmp_path / "dest"

    staging.stage_game(game, dest, rtp=rtp)

    assert (dest / "shared.png").read_text() == "from-rtp"
    assert (dest / "RPG_RT.ldb").read_text() == "game-version"


def test_stage_custom_exclude_path(tmp_path):
    game = tmp_path / "game"
    game.mkdir()
    _make_game(game)
    dest = tmp_path / "dest"

    staging.stage_game(game, dest, exclude_paths=["CharSet/Hero.png"])

    assert not (dest / "CharSet" / "Hero.png").exists()
    assert (dest / "RPG_RT.ldb").exists()
