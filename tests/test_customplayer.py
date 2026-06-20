import json
import pytest

import customplayer


def test_check_env_no_docker_raises(monkeypatch):
    monkeypatch.setattr(customplayer.shutil, "which", lambda _x: None)
    with pytest.raises(customplayer.BuildEnvError):
        customplayer.check_env()


def test_rebuild_no_docker_raises(monkeypatch):
    monkeypatch.setattr(customplayer.shutil, "which", lambda _x: None)
    with pytest.raises(customplayer.BuildEnvError):
        customplayer.rebuild_custom_player(
            "tid", [{"label": "頁１", "chars": "甲乙"}])


def test_engine_dir_and_has_engine(monkeypatch, tmp_path):
    monkeypatch.setattr(customplayer, "CUSTOM_DIR", tmp_path)
    d = customplayer.engine_dir("abc")
    assert d == tmp_path / "abc"
    assert customplayer.has_engine("abc") is False
    d.mkdir()
    for f in customplayer.PLAYER_FILES:
        (d / f).write_text("x")
    assert customplayer.has_engine("abc") is True


def test_is_current(monkeypatch, tmp_path):
    monkeypatch.setattr(customplayer, "CUSTOM_DIR", tmp_path)
    table = {"id": "abc", "name": "甲",
             "pages": [{"label": "頁１", "chars": "甲乙"},
                       {"label": "頁２", "chars": "丙"}]}
    assert customplayer.is_current(table) is False           # 還沒編
    d = tmp_path / "abc"
    d.mkdir()
    for f in customplayer.PLAYER_FILES:                      # has_engine 需要這三個檔
        (d / f).write_text("x")
    (d / "source.json").write_text(
        json.dumps({"pages": [{"label": "頁１", "chars": "甲乙"},
                              {"label": "頁２", "chars": "丙"}]}), encoding="utf-8")
    assert customplayer.is_current(table) is True            # 內容相符
    table["pages"][0]["chars"] = "改了"
    assert customplayer.is_current(table) is False           # 內容變了 → 過期


def test_is_current_corrupt_source_json(monkeypatch, tmp_path):
    """source.json 損壞時 is_current 應回 False（即使引擎檔存在）。"""
    monkeypatch.setattr(customplayer, "CUSTOM_DIR", tmp_path)
    d = tmp_path / "abc"
    d.mkdir()
    for f in customplayer.PLAYER_FILES:
        (d / f).write_text("x")
    (d / "source.json").write_text("{not json", encoding="utf-8")
    assert customplayer.is_current(
        {"id": "abc", "pages": [{"label": "頁１", "chars": "甲"}]}) is False
