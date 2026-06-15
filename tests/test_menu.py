from pathlib import Path

import menu


def test_write_menu_generates_grid(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    entries = [
        {"label": "花嫁之冠", "slug": "花嫁之冠", "cover_rel": "games/花嫁之冠/cover.png"},
        {"label": "A & B", "slug": "a-b", "cover_rel": None},
    ]

    out = menu.write_menu(dist, "我的遊戲庫", entries)

    assert out == dist / "index.html"
    html = out.read_text(encoding="utf-8")
    assert "我的遊戲庫" in html
    assert "play.html?game=%E8%8A%B1%E5%AB%81%E4%B9%8B%E5%86%A0" in html
    assert "games/花嫁之冠/cover.png" in html
    assert "icons/icon.png" in html
    assert "A &amp; B" in html
    assert 'rel="manifest"' in html
    assert "serviceWorker" in html


def test_write_menu_one_card_per_entry(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    entries = [
        {"label": "G1", "slug": "g1", "cover_rel": None},
        {"label": "G2", "slug": "g2", "cover_rel": None},
        {"label": "G3", "slug": "g3", "cover_rel": None},
    ]
    out = menu.write_menu(dist, "Lib", entries)
    html = out.read_text(encoding="utf-8")
    assert html.count('class="card"') == 3
