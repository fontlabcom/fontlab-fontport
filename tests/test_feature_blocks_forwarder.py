# this_file: tests/test_feature_blocks_forwarder.py
"""Legacy feature helpers resolve lazily and keep normal module semantics."""

import importlib
import subprocess
import sys
from types import SimpleNamespace

import pytest


def test_feature_forwarder_when_cold_imported_then_no_app_or_host_loads():
    subprocess.run(
        [
            sys.executable,
            "-c",
            """
import sys
class NoApp:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] == 'fontlabapp':
            raise AssertionError('App must stay optional')
sys.meta_path.insert(0, NoApp())
import fontlab_fontport, fontlab_fontport.designspace
import fontlab_fontport.feature_blocks as blocks
assert blocks.__all__ == ['read_feature_blocks', 'write_feature_blocks']
assert 'read_feature_blocks' in dir(blocks)
assert not any(n.split('.')[0] in {'fontlabapp', 'fontlab', 'PythonQt'} for n in sys.modules)
""",
        ],
        check=True,
    )


def test_feature_forwarder_when_helpers_read_then_resolves_the_new_module(monkeypatch):
    blocks = importlib.import_module("fontlab_fontport.feature_blocks")
    read, write = object(), object()
    target = SimpleNamespace(read_feature_blocks=read, write_feature_blocks=write)
    calls = []

    def resolve(name):
        calls.append(name)
        return target

    monkeypatch.setattr(importlib, "import_module", resolve)
    assert blocks.read_feature_blocks is read
    assert blocks.write_feature_blocks is write
    scope = {}
    exec("from fontlab_fontport.feature_blocks import *", scope)
    assert scope["read_feature_blocks"] is read
    assert scope["write_feature_blocks"] is write
    assert calls == ["fontlabapp.fontui.feature_blocks"] * 4
    assert "Deprecated" in blocks.__doc__


def test_feature_forwarder_when_unknown_name_read_then_attribute_error():
    blocks = importlib.import_module("fontlab_fontport.feature_blocks")
    with pytest.raises(AttributeError, match="unknown"):
        _ = blocks.unknown
