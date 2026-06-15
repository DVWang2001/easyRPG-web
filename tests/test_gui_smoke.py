import importlib

import easyrpg_web_build as core


def test_gui_imports_and_references_core():
    mod = importlib.import_module("easyrpg_web_gui")
    assert mod.core is core
    assert hasattr(mod, "App")
    assert callable(core.build)
