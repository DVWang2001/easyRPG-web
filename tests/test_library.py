from pathlib import Path

import library


def _game(root: Path, marker: str):
    root.mkdir()
    (root / "RPG_RT.ldb").write_text(marker)


def test_stage_library_two_games(tmp_path):
    out = tmp_path / "dist"
    g1 = tmp_path / "g1"
    _game(g1, "one")
    g2 = tmp_path / "g2"
    _game(g2, "two")
    cover = tmp_path / "c.png"
    cover.write_bytes(b"\x89PNG")
    sf = tmp_path / "sf.sf2"
    sf.write_bytes(b"SF2")
    games = [
        {"folder": g1, "label": "Game One", "slug": "game-one", "cover": cover,
         "tags": ["RPG", "漢化"]},
        {"folder": g2, "label": "Game Two", "slug": "game-two", "cover": None},
    ]

    entries = library.stage_library(out, games, soundfont=sf)

    assert (out / "games" / "game-one" / "index.json").exists()
    assert (out / "games" / "game-one" / "easyrpg.soundfont").exists()
    assert (out / "games" / "game-two" / "index.json").exists()
    assert (out / "games" / "game-one" / "cover.png").read_bytes() == b"\x89PNG"
    assert not (out / "games" / "game-two" / "cover.png").exists()
    assert entries[0] == {"label": "Game One", "slug": "game-one",
                          "cover_rel": "games/game-one/cover.png",
                          "tags": ["RPG", "漢化"]}
    # 未給 tags → 空清單
    assert entries[1] == {"label": "Game Two", "slug": "game-two",
                          "cover_rel": None, "tags": []}


def test_stage_library_cover_not_in_index_json(tmp_path):
    out = tmp_path / "dist"
    g1 = tmp_path / "g1"
    _game(g1, "one")
    cover = tmp_path / "c.png"
    cover.write_bytes(b"\x89PNG")
    games = [{"folder": g1, "label": "G", "slug": "g", "cover": cover}]

    library.stage_library(out, games, soundfont=None)

    import json
    idx = json.loads((out / "games" / "g" / "index.json").read_text(encoding="utf-8"))
    assert "cover" not in idx["cache"]


def test_stage_library_with_rtp(tmp_path):
    out = tmp_path / "dist"
    g1 = tmp_path / "g1"
    g1.mkdir()
    (g1 / "RPG_RT.ldb").write_text("game-version")
    rtp = tmp_path / "rtp"
    rtp.mkdir()
    (rtp / "shared.png").write_text("from-rtp")
    (rtp / "RPG_RT.ldb").write_text("rtp-version")
    games = [{"folder": g1, "label": "G", "slug": "g", "cover": None, "rtp": rtp}]

    library.stage_library(out, games, soundfont=None)

    assert (out / "games" / "g" / "shared.png").read_text() == "from-rtp"
    assert (out / "games" / "g" / "RPG_RT.ldb").read_text() == "game-version"
