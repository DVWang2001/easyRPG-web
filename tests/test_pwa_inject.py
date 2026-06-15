from pathlib import Path

import pwa


def test_inject_play_game_info(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "play.html").write_text(
        "<html><head></head><body></body></html>", encoding="utf-8"
    )
    entries = [
        {"label": "花嫁之冠", "slug": "game", "cover_rel": "games/game/cover.png"},
        {"label": "勇者傳說", "slug": "game-2", "cover_rel": None},
    ]

    out = pwa.inject_play_game_info(dist, entries)

    assert out == dist / "play.html"
    html = (dist / "play.html").read_text(encoding="utf-8")
    assert "__EASYRPG_GAMES__" in html
    assert "花嫁之冠" in html
    assert "勇者傳說" in html
    assert "games/game/cover.png" in html
    assert "games/game-2" not in html
    assert "document.title" in html
    assert "icon" in html
    assert html.count("</head>") == 1


def test_inject_escapes_angle_bracket(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "play.html").write_text("<head></head>", encoding="utf-8")
    entries = [{"label": "a</script>b", "slug": "g", "cover_rel": None}]

    pwa.inject_play_game_info(dist, entries)

    html = (dist / "play.html").read_text(encoding="utf-8")
    assert "a\\u003c/script>b" in html
