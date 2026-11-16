# this_file: tests/test_ui_tombstones.py
"""Old Fontport editor imports fail with the corresponding App home."""

import importlib
import importlib.machinery
import importlib.util
import sys

import pytest

PEERS = ("fontlabapp", "fontlab_glyport")

FONTUI_HOME = "fontlabapp.fontui"
FONTUI_FACTORIES = (
    "font_info_editor",
    "groups_editor",
    "kerning_editor",
    "transform_editor",
    "batch_panel",
    "glyph_sequence",
)
FONTUI_MODULES = (
    "fontinfo",
    "groups",
    "groups_view",
    "kerning",
    "kerning_view",
    "transform",
    "transform_view",
    "batch",
    "batch_worker",
    "sequence",
)
HOME_PATTERN = FONTUI_HOME.replace(".", r"\.")


@pytest.mark.parametrize("name", FONTUI_FACTORIES)
def test_fontui_when_removed_factory_imported_then_error_names_fontport_ui(name):
    with pytest.raises(ImportError) as info:
        exec(f"from fontlab_fontport.ui import {name}", {})
    assert f"{FONTUI_HOME}.{name}" in str(info.value), str(info.value)


@pytest.mark.parametrize("name", FONTUI_FACTORIES)
def test_fontui_when_removed_factory_read_as_attribute_then_import_error(name):
    fontui = importlib.import_module("fontlab_fontport.ui")
    with pytest.raises(ImportError, match=HOME_PATTERN):
        getattr(fontui, name)


@pytest.mark.parametrize("name", FONTUI_MODULES)
def test_fontui_when_removed_module_name_imported_then_error_names_fontport_ui(name):
    with pytest.raises(ImportError, match=HOME_PATTERN):
        exec(f"from fontlab_fontport.ui import {name}", {})
    with pytest.raises(ImportError):
        importlib.import_module(f"fontlab_fontport.ui.{name}")


@pytest.mark.parametrize("name", FONTUI_MODULES)
def test_fontui_when_moved_submodule_imported_then_error_names_its_new_module(name):
    with pytest.raises(ImportError) as info:
        importlib.import_module(f"fontlab_fontport.ui.{name}")
    assert f"{FONTUI_HOME}.{name}" in str(info.value), str(info.value)
    assert info.value.name == f"fontlab_fontport.ui.{name}", info.value.name


def test_fontui_when_moved_submodule_statement_used_then_error_names_new_module():
    with pytest.raises(ImportError, match=r"fontlab_fontport\.ui\.kerning\b"):
        exec("import fontlab_fontport.ui.kerning", {})


def test_fontui_when_unknown_or_kept_submodule_imported_then_normal_import_rules():
    with pytest.raises(ModuleNotFoundError) as info:
        importlib.import_module("fontlab_fontport.ui.no_such_module")
    assert FONTUI_HOME not in str(info.value), "only moved names get the hint"


@pytest.mark.parametrize("name", FONTUI_FACTORIES)
def test_fontui_when_factory_name_imported_as_submodule_then_plain_module_not_found(
    name,
):
    """Factories were never modules: the finder answers module names only."""
    with pytest.raises(ModuleNotFoundError) as info:
        importlib.import_module(f"fontlab_fontport.ui.{name}")
    assert FONTUI_HOME not in str(info.value), str(info.value)


def test_fontui_when_find_spec_asks_for_moved_module_then_import_error_not_none():
    """Documented deviation: find_spec raises the hint instead of returning None."""
    with pytest.raises(ImportError, match=r"fontlab_fontport\.ui\.kerning\b"):
        importlib.util.find_spec("fontlab_fontport.ui.kerning")


def test_fontui_when_moved_sets_read_then_moved_is_factories_plus_modules():
    fontui = importlib.import_module("fontlab_fontport.ui")
    assert frozenset(FONTUI_FACTORIES) | frozenset(FONTUI_MODULES) == fontui.MOVED
    assert "MOVED" not in fontui.__all__ and "MOVED_HOME" not in fontui.__all__


def test_fontui_when_tombstone_finder_installed_twice_then_one_finder():
    fontui = importlib.import_module("fontlab_fontport.ui")
    fontui._install_moved_finder()
    fontui._install_moved_finder()
    marked = [f for f in sys.meta_path if getattr(f, fontui._FINDER_MARK, False)]
    assert len(marked) == 1, marked
    path_finder = sys.meta_path.index(importlib.machinery.PathFinder)
    assert sys.meta_path.index(marked[0]) > path_finder, (
        "consulted only after files miss"
    )


def test_fontui_when_removed_name_hit_then_no_peer_package_is_loaded():
    before = set(sys.modules)
    with pytest.raises(ImportError):
        exec("from fontlab_fontport.ui import kerning_editor", {})
    leaked = {n for n in set(sys.modules) - before if n.split(".")[0] in PEERS}
    assert not leaked, leaked


def test_fontui_when_unknown_name_read_then_attribute_error_not_tombstone():
    fontui = importlib.import_module("fontlab_fontport.ui")
    with pytest.raises(AttributeError):
        fontui.no_such_name  # noqa: B018 - the attribute read is the subject


def test_ui_when_all_read_then_no_editor_is_exported():
    ui = importlib.import_module("fontlab_fontport.ui")
    assert not ui.__all__
