import pytest

import customplayer


def test_check_env_raises_without_docker(monkeypatch):
    monkeypatch.setattr(customplayer.shutil, "which", lambda _x: None)
    with pytest.raises(customplayer.BuildEnvError):
        customplayer.check_env()


def test_rebuild_raises_without_docker(monkeypatch):
    monkeypatch.setattr(customplayer.shutil, "which", lambda _x: None)
    with pytest.raises(customplayer.BuildEnvError):
        customplayer.rebuild_custom_player("甲乙", "丙丁")
