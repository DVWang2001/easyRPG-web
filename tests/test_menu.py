from pathlib import Path

import menu


def test_write_menu_generates_grid(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    entries = [
        {"label": "花嫁之冠", "slug": "game", "cover_rel": "games/game/cover.png"},
        {"label": "A & B", "slug": "a-b", "cover_rel": None},
    ]

    out = menu.write_menu(dist, "我的遊戲庫", entries)

    assert out == dist / "index.html"
    html = out.read_text(encoding="utf-8")
    assert "我的遊戲庫" in html
    assert 'href="play-game.html"' in html
    assert 'href="play-a-b.html"' in html
    assert "games/game/cover.png" in html
    assert "icons/icon.png" in html
    assert "A &amp; B" in html
    assert 'rel="manifest"' in html
    assert "serviceWorker" in html


def test_write_menu_search_box_tags_and_filter_js(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    entries = [
        {"label": "花嫁之冠", "slug": "game", "cover_rel": "games/game/cover.png",
         "tags": ["RPG", "漢化"]},
        {"label": "Abyss", "slug": "abyss", "cover_rel": None, "tags": ["動作"]},
        {"label": "無標籤", "slug": "x", "cover_rel": None},  # 沒有 tags 鍵
    ]

    out = menu.write_menu(dist, "庫", entries)
    html = out.read_text(encoding="utf-8")

    # 搜尋框
    assert 'id="q"' in html
    # 卡片帶 data-label / data-tags（小寫供比對）
    assert 'data-label="花嫁之冠"' in html
    assert 'data-tags="rpg,漢化"' in html
    assert 'data-tags="動作"' in html
    # 沒有 tags 的卡片 → data-tags=""（不報錯）
    assert 'data-tags=""' in html
    # 頂部標籤篩選列：每個不重複標籤一個按鈕（RPG/漢化/動作 = 3）
    assert html.count('class="tagfilter"') == 3
    # 卡片內也有可點標籤晶片
    assert 'class="tag"' in html
    # 前端篩選 JS 關鍵元素
    assert "selected" in html
    assert "tagfilter" in html
    assert "c.hidden" in html


def test_write_menu_has_card_hover_effect(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    entries = [{"label": "G", "slug": "g", "cover_rel": None, "tags": []}]

    html = menu.write_menu(dist, "Lib", entries).read_text(encoding="utf-8")

    # 圖片包在可裁切的 .thumb 容器（供 zoom 與光澤掃過）
    assert 'class="thumb"' in html
    assert ".thumb img" in html
    # hover 特效只在真有指標懸停的裝置（手機不會卡住）
    assert ".card:hover" in html
    assert "hover: hover" in html or "hover:hover" in html
    # 觸控按壓回饋、鍵盤聚焦、減少動態
    assert ".card:active" in html
    assert "focus-visible" in html
    assert "prefers-reduced-motion" in html


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
