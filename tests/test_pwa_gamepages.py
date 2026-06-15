from pathlib import Path

import pwa

TEMPLATE = (
    "<html><head><title>EasyRPG Player</title></head>"
    "<body><script>createEasyRpgPlayer({ game: undefined, saveFs: undefined });"
    "</script></body></html>"
)


def _write_template(dist: Path):
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "play.html").write_text(TEMPLATE, encoding="utf-8")


def test_write_game_pages_titles_icons_and_baked_game(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    entries = [
        {"label": "花嫁之冠", "slug": "game", "cover_rel": "games/game/cover.png"},
        {"label": "勇者傳說", "slug": "game-2", "cover_rel": None},
    ]

    pwa.write_game_pages(dist, entries)

    a = (dist / "play-game.html").read_text(encoding="utf-8")
    b = (dist / "play-game-2.html").read_text(encoding="utf-8")
    assert "<title>花嫁之冠</title>" in a
    assert "EasyRPG Player" not in a
    assert "<title>勇者傳說</title>" in b
    assert '<link rel="icon" href="games/game/cover.png">' in a
    assert 'rel="apple-touch-icon" href="games/game/cover.png"' in a
    assert '<link rel="icon" href="icons/icon.png">' in b
    assert 'game: "game"' in a
    assert 'game: "game-2"' in b


def test_write_game_pages_escapes_label(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    entries = [{"label": "A & B", "slug": "g", "cover_rel": None}]

    pwa.write_game_pages(dist, entries)

    html = (dist / "play-g.html").read_text(encoding="utf-8")
    assert "<title>A &amp; B</title>" in html
