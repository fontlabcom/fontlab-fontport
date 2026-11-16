# this_file: tests/test_edit_guards_extra.py
"""Native writes name the missing ``fontlab`` extra instead of a bare ModuleNotFoundError."""

import builtins
import sys

import pytest

from fontlab_fontport import host
from fontlab_fontport.errors import UnsupportedCapability


def test_edit_guards_when_app_missing_then_extra_is_named(monkeypatch):
    monkeypatch.setitem(sys.modules, "fontlabapp", None)
    monkeypatch.setitem(sys.modules, "fontlabapp.core.edit_guards", None)
    with pytest.raises(UnsupportedCapability, match=r"fontlab-fontport\[fontlab\]"):
        host._edit_guards()


def test_edit_guards_when_app_present_then_module_is_returned(monkeypatch):
    import fontlabapp.core as core

    guards = type(sys)("fontlabapp.core.edit_guards")
    monkeypatch.setattr(core, "edit_guards", guards, raising=False)
    monkeypatch.setitem(sys.modules, "fontlabapp.core.edit_guards", guards)
    assert host._edit_guards() is guards


@pytest.mark.parametrize("name", ["fontlabapp_dependency", "fontgate", None])
def test_edit_guards_when_other_module_missing_then_original_error_is_raised(
    monkeypatch, name
):
    original_import = builtins.__import__
    missing = ModuleNotFoundError("missing dependency", name=name)

    def import_with_missing_dependency(module, *args, **kwargs):
        if module == "fontlabapp.core.edit_guards":
            raise missing
        return original_import(module, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_with_missing_dependency)
    with pytest.raises(ModuleNotFoundError) as caught:
        host._edit_guards()
    assert caught.value is missing, "Keep the original dependency error and traceback"


@pytest.mark.parametrize("name", ["fontlabapp", "fontlabapp.core.edit_guards"])
def test_edit_guards_when_app_module_missing_then_extra_error_keeps_cause(
    monkeypatch, name
):
    original_import = builtins.__import__
    missing = ModuleNotFoundError("missing App module", name=name)

    def import_without_app(module, *args, **kwargs):
        if module == "fontlabapp.core.edit_guards":
            raise missing
        return original_import(module, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_app)
    with pytest.raises(UnsupportedCapability, match=r"fontlab-fontport\[fontlab\]") as caught:
        host._edit_guards()
    assert caught.value.__cause__ is missing, "Keep the missing App module as the cause"
