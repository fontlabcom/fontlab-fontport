# this_file: tests/test_review_regressions.py
"""Round-2 probes from X3's independent review."""

import sys
from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_world import Host

from fontlab_fontport.batch import BatchRunner
from fontlab_fontport.host import NativeFontBackend
from fontlab_fontport.info import stage_info
from fontlab_fontport.live import RFont
from fontlab_fontport.recipe import Recipe
from fontlab_fontport.world import FontWorld, register


@pytest.fixture
def native_lib(monkeypatch):
    events = []
    package = SimpleNamespace(
        packageLib={},
        mastersContainer=lambda: "masters",
        checkInitHistoryState=lambda index: events.append(("prepare", index)),
    )
    backend = object.__new__(NativeFontBackend)
    backend._package = lambda: package
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flItems=SimpleNamespace(
                notifyChangesApplied=lambda name, objects: events.append(
                    (name, objects, deepcopy(package.packageLib))
                )
            )
        ),
    )
    return RFont(backend), package, events


@pytest.mark.parametrize(
    "foreign",
    [
        "x\r\ny\rz",
        None,
        2**53 + 1,
        "control\x01text",
        {"null": None, "text": "\r\n", "big": 2**60},
    ],
)
def test_native_lib_when_unrelated_write_then_foreign_values_survive(
    native_lib, foreign
):
    font, package, events = native_lib
    package.packageLib = {"foreign": foreign}
    assert font.lib["foreign"] == foreign
    assert dict(font.lib) == {"foreign": foreign}
    font.lib["new"] = "kept\r\nexact\r"
    assert package.packageLib == {"foreign": foreign, "new": "kept\r\nexact\r"}
    assert events[-1][1] == [package, "masters"]
    before = deepcopy(package.packageLib), list(events)
    font.lib["new"] = "kept\r\nexact\r"
    assert (package.packageLib, events) == before, "identical edits add no history"
    with pytest.raises((TypeError, NotImplementedError)):
        font.lib.update({"valid": 2, "bad": None})
    assert (package.packageLib, events) == before
    del font.lib["new"]
    assert package.packageLib == {"foreign": foreign}
    font.lib.clear()
    assert package.packageLib == {}


def test_native_lib_when_new_big_integer_then_refused_without_history(native_lib):
    font, package, events = native_lib
    with pytest.raises(ValueError, match="exact JSON"):
        font.lib["big"] = 2**53 + 1
    assert not package.packageLib and not events


@pytest.mark.parametrize("foreign", [None, 2**60, "x\r\ny\rz", "c\x01"])
@pytest.mark.parametrize("direct_backend", [False, True])
def test_native_lib_when_nested_sibling_edited_then_foreign_leaf_preserved(
    native_lib, foreign, direct_backend
):
    font, package, events = native_lib
    package.packageLib = {"nested": {"foreign": foreign, "valid": 1}}
    value = font.lib["nested"]
    value["valid"] = 2
    if direct_backend:
        font._backend.set_lib({"nested": value})
    else:
        font.lib["nested"] = value
    assert package.packageLib == {"nested": {"foreign": foreign, "valid": 2}}
    assert events[-1][1] == [package, "masters"]
    before = deepcopy(package.packageLib), list(events)
    value["new-null"] = None
    with pytest.raises((TypeError, NotImplementedError)):
        font.lib["nested"] = value
    assert (package.packageLib, events) == before


def test_native_lib_when_array_sibling_edited_then_unchanged_null_preserved(native_lib):
    font, package, events = native_lib
    package.packageLib = {"nested": {"items": [None, 1]}}
    font.lib["nested"] = {"items": [None, 2]}
    assert package.packageLib == {"nested": {"items": [None, 2]}}
    before = deepcopy(package.packageLib), list(events)
    with pytest.raises((TypeError, NotImplementedError)):
        font.lib["nested"] = {"items": [None, 2, None]}
    assert (package.packageLib, events) == before


def test_batch_when_called_then_preflight_and_reservation_are_immediate(tmp_path):
    runner = BatchRunner()
    with pytest.raises(FileNotFoundError):
        runner.run([(tmp_path / "missing.ufo", tmp_path / "out.ufo")], Recipe())
    source = tmp_path / "source.ufo"
    source.mkdir()
    iterator = runner.run([(source, tmp_path / "out.ufo")], Recipe())
    assert runner.running
    with pytest.raises(RuntimeError, match="running"):
        runner.run([(source, tmp_path / "other.ufo")], Recipe())
    iterator.close()
    assert not runner.running, "close before first next must release the reservation"
    with pytest.raises(ValueError, match="Duplicate"):
        runner.run(
            [(source, tmp_path / "A.ufo"), (source, tmp_path / "a.ufo")], Recipe()
        )


def test_panose_when_value_is_256_then_refused():
    with pytest.raises(ValueError, match="255"):
        stage_info({"openTypeOS2Panose": [256] * 10}, "Edit")


def test_world_when_owned_id_reused_then_replace_and_invalidate_cached_borrower(
    tmp_path,
):
    host = Host()
    environment = FontWorld(host)
    old = environment.CurrentFont()
    host.open_font = lambda path: 1
    opened = environment.OpenFont(str(tmp_path / "owned.vfj"))
    assert opened is not old and opened._backend.owned
    with pytest.raises(RuntimeError, match="closed"):
        old.keys()


def test_register_when_upstream_key_missing_then_restores_absence(monkeypatch):
    from fontParts import world

    monkeypatch.delitem(world.dispatcher._registry, "CurrentGuidelines")
    with register(FontWorld(Host())), pytest.raises(NotImplementedError):
        world.CurrentGuidelines()
    assert "CurrentGuidelines" not in world.dispatcher._registry


def test_native_info_when_tuple_readback_equals_list_then_no_history(monkeypatch):
    events = []
    package = SimpleNamespace(
        info=SimpleNamespace(openTypeOS2Panose=(2,) * 10),
        panose="2 2 2 2 2 2 2 2 2 2",
        checkInitHistoryState=lambda _: events.append("history"),
    )
    backend = object.__new__(NativeFontBackend)
    backend._package = lambda: package
    backend.set_info_many({"openTypeOS2Panose": [2] * 10})
    assert backend.get_info("openTypeOS2Panose") == [2] * 10
    assert not events


def test_host_facing_paths_when_relative_then_refused_before_side_effects(
    monkeypatch, tmp_path
):
    from test_export import Backend

    from fontlab_fontport.application import NativeApplication
    from fontlab_fontport.export import compile_ttf, export_ufo_subset

    monkeypatch.chdir(tmp_path)
    (tmp_path / "source.ufo").mkdir()
    backend = object.__new__(NativeFontBackend)
    backend._package = lambda: SimpleNamespace(path="relative.vfj")
    backend._saved_path = None
    actions = [
        lambda: NativeApplication().open_font("relative.vfj"),
        lambda: BatchRunner().run([("source.ufo", tmp_path / "out.ufo")], Recipe()),
        lambda: BatchRunner().run([(tmp_path / "source.ufo", "out.ufo")], Recipe()),
        lambda: export_ufo_subset(
            Backend(), ["A"], "relative.ufo", family_name="Owned"
        ),
        lambda: compile_ttf("source.ufo", tmp_path / "out.ttf"),
        lambda: backend.save("relative.vfj"),
        lambda: backend.save(),
    ]
    for action in actions:
        with pytest.raises(ValueError, match="absolute"):
            action()
    assert not (tmp_path / "out.ufo").exists() and not (tmp_path / "out.ttf").exists()


def test_active_font_when_none_but_fonts_open_then_none_or_real_error(monkeypatch):
    from fontlab_fontport.application import NativeApplication

    class NativeError(RuntimeError):
        pass

    def call(name):
        if name == "list_fonts":
            return {"fonts": [{"id": 1}]}
        raise NativeError("No active font.")

    monkeypatch.setitem(
        sys.modules, "fontpr", SimpleNamespace(call=call, Error=NativeError)
    )
    assert NativeApplication().current_font_id() is None


def test_structured_readback_when_tuple_records_and_stems_then_detached_lists():
    record = {
        "nameID": 256,
        "platformID": 3,
        "encodingID": 1,
        "languageID": 1033,
        "string": "Ω",
    }
    backend = object.__new__(NativeFontBackend)
    backend._package = lambda: SimpleNamespace(
        info=SimpleNamespace(
            openTypeNameRecords=(record,), postscriptStemSnapH=(20.5, 80)
        )
    )
    assert backend.get_info("postscriptStemSnapH") == [20.5, 80]
    result = backend.get_info("openTypeNameRecords")
    result[0]["string"] = "changed"
    assert record["string"] == "Ω"


def test_batch_when_old_iterator_closed_twice_then_new_reservation_survives(tmp_path):
    source = tmp_path / "source.ufo"
    source.mkdir()
    runner = BatchRunner()
    old = runner.run([(source, tmp_path / "old.ufo")], Recipe())
    old.close()
    new = runner.run([(source, tmp_path / "new.ufo")], Recipe())
    old.close()
    assert runner.running
    new.close()
    assert not runner.running


def test_stage_lib_when_cr_and_crlf_then_no_xml_readback_normalization():
    from fontlab_fontport.fontdata import stage_lib

    assert stage_lib({"text": "x\r\ny\rz"}) == {"text": "x\r\ny\rz"}


def test_native_lib_when_numeric_type_changes_then_not_an_identical_edit(native_lib):
    font, package, events = native_lib
    package.packageLib = {"value": {"items": [1]}, "foreign": None}
    font.lib["value"] = {"items": [True]}
    assert package.packageLib["value"]["items"][0] is True
    assert events and package.packageLib["foreign"] is None
