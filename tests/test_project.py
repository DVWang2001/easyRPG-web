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
