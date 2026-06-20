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
    '<body><script async type="text/javascript" src="index.js"></script>'
    "<script>createEasyRpgPlayer({ game: undefined, saveFs: undefined });"
    "</script></body></html>"
)


def _write_template(dist: Path):
    dist.mkdir(parents=True, exist_ok=True)
    (dist / "play.html").write_text(TEMPLATE, encoding="utf-8")


def test_write_game_pages_injects_save_ui(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    pwa.write_game_pages(dist, [{"label": "甲", "slug": "g", "cover_rel": None}])
    html = (dist / "play-g.html").read_text(encoding="utf-8")
    # 左上角存檔面板：兩個按鈕 + 檔案輸入
    assert 'id="saveui"' in html
    assert "導出存檔" in html and "導入存檔" in html
    assert 'id="savefile"' in html
    # 非全螢幕才顯示（fullscreenchange 控制）
    assert "fullscreenchange" in html and "fullscreenElement" in html
    # 存檔資料夾＝/easyrpg/<game>/Save（找不到再走訪 FS）；整包 zip；導入後 syncfs + reload
    assert "/easyrpg/" in html and "/Save" in html
    assert "walkDir" in html and "saveDir" in html
    assert "makeZip" in html and "syncfs" in html and "location.reload" in html
    # 每頁帶自己的 slug 當下載檔名
    assert 'SLUG="g"' in html or 'SLUG = "g"' in html


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
    # 每遊戲獨立身分：id 與收窄的 scope（避免 Android Chrome 把各遊戲視為同一 App）
    assert m["id"] == "play-game.html"
    assert m["scope"] == "play-game.html"
    # 無封面者 manifest icons 退回庫主圖示
    m2 = json.loads((dist / "manifest-game-2.webmanifest").read_text(encoding="utf-8"))
    assert all(icon["src"] == "icons/icon.png" for icon in m2["icons"])
    # 不同遊戲 → 不同 id / 不重疊 scope
    assert m2["id"] == "play-game-2.html"
    assert m2["scope"] == "play-game-2.html"
    assert m2["scope"] != m["scope"]


def test_write_game_pages_per_game_precache(tmp_path):
    # 每個遊戲頁只下載自己：產出 precache-<slug>.json（殼 + 該遊戲所有檔），頁面有下載進度條
    dist = tmp_path / "dist"
    _write_template(dist)
    # 該遊戲的實體檔
    g = dist / "games" / "game"
    g.mkdir(parents=True)
    (g / "RPG_RT.ldb").write_text("x")
    (g / "cover.png").write_bytes(b"\x89PNG")
    sub = g / "CharSet"
    sub.mkdir()
    (sub / "Hero.png").write_bytes(b"png")
    entries = [{"label": "花嫁之冠", "slug": "game", "cover_rel": "games/game/cover.png"}]

    pwa.write_game_pages(dist, entries)

    # 每遊戲 precache 清單：含殼與該遊戲的檔，但「不含」別的遊戲
    files = json.loads((dist / "precache-game.json").read_text(encoding="utf-8"))
    assert "index.wasm" in files
    assert "play-game.html" in files
    assert "manifest-game.webmanifest" in files
    assert "games/game/RPG_RT.ldb" in files
    assert "games/game/CharSet/Hero.png" in files

    page = (dist / "play-game.html").read_text(encoding="utf-8")
    assert 'fetch("precache-"+SLUG+".json")' in page  # 頁面自己抓清單下載
    assert 'caches.open("easyrpg-games")' in page
    assert "下載此遊戲以供離線" in page


def test_write_game_pages_custom_uses_player_custom_engine(tmp_path):
    dist = tmp_path / "dist"
    _write_template(dist)
    entries = [
        {"label": "甲", "slug": "g1", "cover_rel": None, "name_table_id": "tid1"},
        {"label": "乙", "slug": "g2", "cover_rel": None, "name_table_id": ""},
    ]

    pwa.write_game_pages(dist, entries)

    a = (dist / "play-g1.html").read_text(encoding="utf-8")
    b = (dist / "play-g2.html").read_text(encoding="utf-8")
    # 自訂遊戲頁載入 player-custom-<id>/ 引擎；非自訂用根目錄官方引擎
    assert 'src="player-custom-tid1/index.js"' in a
    assert 'src="index.js"' not in a
    assert 'src="index.js"' in b
    assert "player-custom" not in b
    # precache 帶各自的引擎檔
    pa = json.loads((dist / "precache-g1.json").read_text(encoding="utf-8"))
    pb = json.loads((dist / "precache-g2.json").read_text(encoding="utf-8"))
    assert "player-custom-tid1/index.js" in pa and "player-custom-tid1/index.wasm" in pa
    assert "index.js" in pb and "index.wasm" in pb
    assert "player-custom-tid1/index.js" not in pb
    # 自訂(SDL3)頁注入 canvas 撐滿覆寫（修「畫面小、黑邊大」）；非自訂頁不注入
    assert "width:100vw" in a and "!important" in a
    assert "100vw" not in b


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
