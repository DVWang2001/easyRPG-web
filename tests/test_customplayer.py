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
        customplayer.rebuild_custom_player("tid", "甲乙", "丙丁")


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
    table = {"id": "abc", "name": "甲", "zh_tw_1": "甲乙", "zh_tw_2": "丙"}
    assert customplayer.is_current(table) is False           # 還沒編
    d = tmp_path / "abc"
    d.mkdir()
    (d / "source.json").write_text(
        json.dumps({"zh_tw_1": "甲乙", "zh_tw_2": "丙"}), encoding="utf-8")
    assert customplayer.is_current(table) is True            # 內容相符
    table["zh_tw_1"] = "改了"
    assert customplayer.is_current(table) is False           # 內容變了 → 過期
