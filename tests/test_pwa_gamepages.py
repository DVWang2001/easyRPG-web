import json
from pathlib import Path

import pwa

# 模板模擬 patch_index_html 後的 play.html：含整庫的 manifest / apple-touch-icon / app-title
TEMPLATE = (
    "<html><head>"
    '<link rel="manifest" href="manifest.webmanifest">'
    '<link rel="apple-touch-icon" href="icons/icon.png">'
    '<meta name="apple-mobile-web-app-title" content="RM作品收藏">'
    "<title>EasyRPG Player</title>"
    "</head>"
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


def test_write_game_pages_per_game_manifest_replaces_library(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    entries = [
        {"label": "花嫁之冠", "slug": "game", "cover_rel": "games/game/cover.png"},
        {"label": "勇者傳說", "slug": "game-2", "cover_rel": None},
    ]

    pwa.write_game_pages(dist, entries)

    a = (dist / "play-game.html").read_text(encoding="utf-8")
    # 頁面引用自己的 manifest，整庫的 manifest / apple-touch-icon 已被移除
    assert '<link rel="manifest" href="manifest-game.webmanifest">' in a
    assert 'href="manifest.webmanifest"' not in a
    assert 'href="icons/icon.png"' not in a  # 庫的 apple-touch-icon 不再殘留
    # app 名稱（加入主畫面的標籤）＝遊戲名
    assert '<meta name="apple-mobile-web-app-title" content="花嫁之冠">' in a
    assert "RM作品收藏" not in a

    # 每遊戲 manifest 檔內容：icons＝封面、start_url＝該頁
    m = json.loads((dist / "manifest-game.webmanifest").read_text(encoding="utf-8"))
    assert m["name"] == "花嫁之冠"
    assert m["start_url"] == "play-game.html"
    assert all(icon["src"] == "games/game/cover.png" for icon in m["icons"])
    # 無封面者 manifest icons 退回庫主圖示
    m2 = json.loads((dist / "manifest-game-2.webmanifest").read_text(encoding="utf-8"))
    assert all(icon["src"] == "icons/icon.png" for icon in m2["icons"])


def test_write_game_pages_locks_title(tmp_path):
    # EasyRPG 引擎會把 document.title 改成遊戲內建標題；頁面需鎖住成導入名稱
    dist = tmp_path / "dist"
    _write_template(dist)
    entries = [{"label": "花嫁之冠", "slug": "game", "cover_rel": None}]

    pwa.write_game_pages(dist, entries)

    html = (dist / "play-game.html").read_text(encoding="utf-8")
    assert "Object.defineProperty(document,'title'" in html
    assert "MutationObserver" in html
    assert '"花嫁之冠"' in html  # 鎖定的目標名稱（JS 字串字面值）


def test_write_game_pages_escapes_label(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    entries = [{"label": "A & B", "slug": "g", "cover_rel": None}]

    pwa.write_game_pages(dist, entries)

    html = (dist / "play-g.html").read_text(encoding="utf-8")
    assert "<title>A &amp; B</title>" in html
