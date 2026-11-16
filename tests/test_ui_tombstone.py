# this_file: tests/test_ui_tombstone.py
"""Fontport keeps no UI: ``fontlab_fontport.ui`` only raises ImportError (issue 201)."""

import importlib

import pytest

NEW_HOME = "fontlabapp.fontui"


@pytest.mark.parametrize("name", ["kerning_editor", "font_info_editor", "batch_panel"])
def test_ui_when_name_read_then_import_error_names_new_home(name: str) -> None:
    ui = importlib.import_module("fontlab_fontport.ui")
    with pytest.raises(ImportError, match=r"moved to fontlabapp\.fontui"):
        getattr(ui, name)


def test_ui_when_never_existing_name_read_then_attribute_error() -> None:
    """Merge with issue 205: only removed names get the hint, so hasattr works."""
    ui = importlib.import_module("fontlab_fontport.ui")
    with pytest.raises(AttributeError):
        ui.anything  # noqa: B018 - the attribute read is the subject
    assert not hasattr(ui, "anything")


def test_ui_when_from_import_then_import_error_names_new_home() -> None:
    with pytest.raises(ImportError, match=r"fontlabapp\.fontui"):
        exec("from fontlab_fontport.ui import kerning_editor", {})


def test_ui_when_module_imported_then_nothing_else_loads() -> None:
    ui = importlib.import_module("fontlab_fontport.ui")
    assert not hasattr(ui, "__wrapped__"), "dunder probes stay AttributeError"
    assert ui.__doc__ and NEW_HOME in ui.__doc__, "docstring names the new home"
    assert "from fly.ap.fontui import kerning_editor" in ui.__doc__


def test_ui_when_submodule_imported_then_import_error() -> None:
    with pytest.raises(ImportError):
        importlib.import_module("fontlab_fontport.ui.kerning")
