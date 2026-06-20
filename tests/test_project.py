import json

import project


def test_default_project_shape():
    p = project.default_project()
    assert p["version"] == project.VERSION
    assert p["games"] == []
    assert p["out"] == "dist"
    assert isinstance(p["lib_name"], str)


def test_load_missing_returns_default_no_warning(tmp_path):
    proj, warning = project.load_project(tmp_path / "nope.json")
    assert warning is None
    assert proj["games"] == []


def test_load_corrupt_returns_default_with_warning(tmp_path):
    f = tmp_path / "library.json"
    f.write_text("{ not valid json", encoding="utf-8")
    proj, warning = project.load_project(f)
    assert proj["games"] == []
    assert warning is not None  # 不丟例外


def test_load_fills_missing_fields(tmp_path):
    f = tmp_path / "library.json"
    f.write_text(json.dumps({"lib_name": "只給名稱"}), encoding="utf-8")
    proj, warning = project.load_project(f)
    assert warning is None
    assert proj["lib_name"] == "只給名稱"
    assert proj["out"] == "dist"        # 補回預設
    assert proj["games"] == []


def test_save_then_load_roundtrip(tmp_path):
    f = tmp_path / "library.json"
    data = {
        "version": 1, "lib_name": "我的庫", "icon": "i.png",
        "soundfont": "s.sf2", "out": "dist",
        "games": [{"folder": "C:/g/甲", "label": "花嫁之冠", "cover": None, "rtp": None}],
    }
    project.save_project(f, data)
    # 中文不被跳脫成 \uXXXX
    assert "花嫁之冠" in f.read_text(encoding="utf-8")
    proj, warning = project.load_project(f)
    assert warning is None
    assert proj["games"][0]["label"] == "花嫁之冠"
    assert proj["games"][0]["cover"] is None


def test_save_is_atomic_no_tmp_left(tmp_path):
    f = tmp_path / "library.json"
    project.save_project(f, project.default_project())
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "library.json"]
    assert leftovers == []


def test_load_fills_missing_tags_as_empty_list(tmp_path):
    f = tmp_path / "library.json"
    f.write_text(json.dumps({
        "games": [{"folder": "C:/g", "label": "甲"}],
    }), encoding="utf-8")
    proj, warning = project.load_project(f)
    assert warning is None
    assert proj["games"][0]["tags"] == []


def test_tags_roundtrip_normalized(tmp_path):
    f = tmp_path / "library.json"
    data = {
        "version": 1, "lib_name": "庫", "icon": "i", "soundfont": "s", "out": "dist",
        "games": [{"folder": "C:/g", "label": "甲",
                   "cover": None, "rtp": None,
                   "tags": ["RPG", " 漢化 ", "", "神作"]}],  # 含空白/空項
    }
    project.save_project(f, data)
    text = f.read_text(encoding="utf-8")
    assert "漢化" in text  # 中文不被跳脫
    proj, _ = project.load_project(f)
    # 去空白、去空項
    assert proj["games"][0]["tags"] == ["RPG", "漢化", "神作"]


def test_all_tags_defaults_empty():
    assert project.default_project()["all_tags"] == []


def test_all_tags_union_from_games_when_absent(tmp_path):
    # 舊檔沒有 all_tags，但遊戲有 tags → all_tags 自動＝各遊戲 tags 的聯集（保序去重）
    f = tmp_path / "library.json"
    f.write_text(json.dumps({
        "games": [{"folder": "a", "label": "甲", "tags": ["RPG", "漢化"]},
                  {"folder": "b", "label": "乙", "tags": ["漢化", "動作"]}],
    }), encoding="utf-8")
    proj, _ = project.load_project(f)
    assert proj["all_tags"] == ["RPG", "漢化", "動作"]


def test_all_tags_merges_explicit_and_used(tmp_path):
    f = tmp_path / "library.json"
    f.write_text(json.dumps({
        "all_tags": ["A", "A", " B "],  # 含重複與空白
        "games": [{"folder": "g", "label": "甲", "tags": ["B", "C"]}],
    }), encoding="utf-8")
    proj, _ = project.load_project(f)
    # 明確清單先（去重去空白），再補上遊戲用到但不在清單的
    assert proj["all_tags"] == ["A", "B", "C"]


def test_name_tables_default_empty():
    assert project.default_project()["name_tables"] == []


def test_normalized_game_has_name_table_id_not_custom_player(tmp_path):
    # 正規化後的遊戲帶 name_table_id（空字串預設），不再有舊的 custom_player 欄位
    f = tmp_path / "library.json"
    f.write_text(json.dumps({"games": [{"folder": "a", "label": "甲"}]}),
                 encoding="utf-8")
    proj, _ = project.load_project(f)
    g = proj["games"][0]
    assert g["name_table_id"] == ""
    assert "custom_player" not in g


def test_name_tables_roundtrip(tmp_path):
    p = tmp_path / "library.json"
    data = project.default_project()
    data["name_tables"] = [
        {"id": "t1", "name": "甲表", "zh_tw_1": "甲乙丙", "zh_tw_2": "丁戊"},
    ]
    data["games"] = [{"folder": "a", "label": "遊戲甲", "name_table_id": "t1"}]
    project.save_project(p, data)
    proj, _ = project.load_project(p)
    assert proj["name_tables"][0] == {
        "id": "t1", "name": "甲表", "zh_tw_1": "甲乙丙", "zh_tw_2": "丁戊"}
    assert proj["games"][0]["name_table_id"] == "t1"


def test_game_name_table_id_dropped_when_table_missing(tmp_path):
    p = tmp_path / "library.json"
    data = project.default_project()
    data["games"] = [{"folder": "a", "label": "x", "name_table_id": "nope"}]
    project.save_project(p, data)
    proj, _ = project.load_project(p)
    # 參照不存在的字表 → 設回空字串
    assert proj["games"][0]["name_table_id"] == ""


def test_legacy_name_table_migrates_to_one_table(tmp_path):
    p = tmp_path / "library.json"
    # 舊格式：單一 name_table 物件 + 遊戲 custom_player 布林
    legacy = {
        "version": 1, "lib_name": "L", "icon": "i", "soundfont": "s", "out": "dist",
        "name_table": {"zh_tw_1": "甲乙", "zh_tw_2": "丙"},
        "games": [
            {"folder": "a", "label": "舊自訂", "custom_player": True},
            {"folder": "b", "label": "舊一般", "custom_player": False},
        ],
    }
    p.write_text(__import__("json").dumps(legacy, ensure_ascii=False), encoding="utf-8")
    proj, _ = project.load_project(p)
    tables = proj["name_tables"]
    assert len(tables) == 1
    assert tables[0]["name"] == "自訂字表"
    assert tables[0]["zh_tw_1"] == "甲乙" and tables[0]["zh_tw_2"] == "丙"
    mid = tables[0]["id"]
    assert proj["games"][0]["name_table_id"] == mid   # custom_player True → 指向遷移字表
    assert proj["games"][1]["name_table_id"] == ""     # False → 空


def test_legacy_empty_name_table_no_migration(tmp_path):
    p = tmp_path / "library.json"
    legacy = {"version": 1, "name_table": {"zh_tw_1": "", "zh_tw_2": ""},
              "games": [{"folder": "a", "label": "x"}]}
    p.write_text(__import__("json").dumps(legacy, ensure_ascii=False), encoding="utf-8")
    proj, _ = project.load_project(p)
    assert proj["name_tables"] == []
    assert proj["games"][0]["name_table_id"] == ""


def test_all_tags_roundtrip(tmp_path):
    f = tmp_path / "library.json"
    data = project.default_project()
    data["all_tags"] = ["RPG", "漢化"]
    project.save_project(f, data)
    assert "漢化" in f.read_text(encoding="utf-8")
    proj, _ = project.load_project(f)
    assert proj["all_tags"] == ["RPG", "漢化"]


def test_missing_sources_flags_empty_and_invalid(tmp_path):
    good = tmp_path / "Good"
    good.mkdir()
    (good / "RPG_RT.ldb").write_bytes(b"x")
    games = [
        {"folder": "", "label": "草稿甲", "cover": None, "rtp": None},
        {"folder": str(tmp_path / "NotExist"), "label": "壞乙", "cover": None, "rtp": None},
        {"folder": str(good), "label": "正常丙", "cover": None, "rtp": None},
    ]
    bad = project.missing_sources(games)
    assert bad == ["草稿甲", "壞乙"]


def test_missing_sources_all_valid_returns_empty(tmp_path):
    g = tmp_path / "G"
    g.mkdir()
    (g / "RPG_RT.lmt").write_bytes(b"x")
    assert project.missing_sources(
        [{"folder": str(g), "label": "丁", "cover": None, "rtp": None}]) == []
