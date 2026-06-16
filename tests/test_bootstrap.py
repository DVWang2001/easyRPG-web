import bootstrap

# 與 menu.py 產生的卡片格式一致：
#   <a class="card" href="play-<slug>.html"><img src="<cover>" alt=""><span><label></span></a>
MENU = """<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<title>RM作品收藏</title>
</head><body><header>RM作品收藏</header><div class="grid">
<a class="card" href="play-2003-i.html"><img src="games/2003-i/cover.png" alt=""><span>2003月藍傳奇Ｉ～異界來的訪客</span></a>
<a class="card" href="play-game.html"><img src="games/game/cover.png" alt=""><span>花嫁之冠</span></a>
<a class="card" href="play-g.html"><img src="icons/icon.png" alt=""><span>A &amp; B</span></a>
</div></body></html>
"""


def test_draft_parses_title_and_games():
    draft = bootstrap.draft_project_from_menu(MENU)
    assert draft["lib_name"] == "RM作品收藏"
    assert len(draft["games"]) == 3
    labels = [g["label"] for g in draft["games"]]
    assert labels == ["2003月藍傳奇Ｉ～異界來的訪客", "花嫁之冠", "A & B"]  # 實體還原


def test_draft_games_have_empty_folder_and_null_cover():
    draft = bootstrap.draft_project_from_menu(MENU)
    for g in draft["games"]:
        assert g["folder"] == ""
        assert g["cover"] is None
        assert g["rtp"] is None


def test_draft_empty_menu_keeps_title():
    html = "<html><head><title>空庫</title></head><body><div class='grid'></div></body></html>"
    draft = bootstrap.draft_project_from_menu(html)
    assert draft["lib_name"] == "空庫"
    assert draft["games"] == []
