# this_file: tests/test_stemsnap_history.py
"""Issue 250 N3: stem-snap info writes refuse unless the font is active and has no unsaved history."""

import sys
from types import SimpleNamespace

import pytest

from fontlab_fontport.capabilities import NATIVE_CAPABILITIES
from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.host import NativeFontBackend

FONT_ID = 7
OTHER = object()


def _backend(monkeypatch, *, dirty, current="self"):
    events = []
    package = SimpleNamespace(
        fgId=FONT_ID,
        info=SimpleNamespace(
            postscriptStemSnapH=[80],
            postscriptStemSnapV=[90],
            familyName="Fam",
        ),
        getProperty=lambda name: events.append(("probe", name)) or dirty,
        checkInitHistoryState=lambda _: events.append("prepare"),
        mastersContainer=lambda: "masters",
    )
    backend = NativeFontBackend.__new__(NativeFontBackend)
    backend._package = lambda: package
    if current == "self":
        current = package
    elif current is OTHER:
        current = SimpleNamespace(fgId=FONT_ID + 1, isNull=False)
    package.isNull = False
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flWorkspace=SimpleNamespace(
                instance=lambda: SimpleNamespace(currentPackage=current)
            ),
            flItems=SimpleNamespace(
                notifyChangesApplied=lambda title, items: events.append(
                    ("notify", title)
                )
            ),
        ),
    )
    return backend, package, events


@pytest.mark.parametrize("field", ["postscriptStemSnapH", "postscriptStemSnapV"])
@pytest.mark.parametrize("dirty", [1, True])
def test_stem_snap_write_when_history_exists_then_refused_before_any_change(
    monkeypatch, field, dirty
):
    backend, package, events = _backend(monkeypatch, dirty=dirty)
    before = (
        list(package.info.postscriptStemSnapH),
        list(package.info.postscriptStemSnapV),
    )
    with pytest.raises(UnsupportedCapability) as error:
        backend.set_info_many({field: [120], "familyName": "Must not write"})
    assert error.value.capability == "info.postscriptStemSnap.history"
    assert field in str(error.value) and "no history or data changed" in str(
        error.value
    )
    assert events == [("probe", "__has_history_changes")], (
        "no checkpoint or notify may run"
    )
    assert (
        package.info.postscriptStemSnapH,
        package.info.postscriptStemSnapV,
    ) == before
    assert package.info.familyName == "Fam", "the whole batch must be refused"


@pytest.mark.parametrize("dirty", [None, 0, False])
def test_stem_snap_write_when_document_clean_then_written_with_checkpoints(
    monkeypatch, dirty
):
    backend, package, events = _backend(monkeypatch, dirty=dirty)
    backend.set_info_many({"postscriptStemSnapV": [120]}, undo_name="stems")
    assert package.info.postscriptStemSnapV == [120]
    assert events == [
        ("probe", "__has_history_changes"),
        "prepare",
        ("notify", "stems"),
        ("notify", "stems"),
    ]


def test_unchanged_stem_snap_in_dirty_document_then_noop_without_refusal(monkeypatch):
    backend, _package, events = _backend(monkeypatch, dirty=1)
    backend.set_info_many({"postscriptStemSnapH": [80], "postscriptStemSnapV": [90]})
    assert events == [], "unchanged values neither probe nor write"


def test_other_info_fields_in_dirty_document_then_not_probed_or_refused(monkeypatch):
    backend, package, events = _backend(monkeypatch, dirty=1)
    backend.set_info_many({"familyName": "New"}, undo_name="fam")
    assert package.info.familyName == "New"
    assert ("probe", "__has_history_changes") not in events


@pytest.mark.parametrize(
    "current",
    [OTHER, None, SimpleNamespace(fgId=FONT_ID, isNull=True)],
    ids=["other-font-active", "no-active-font", "null-active-package"],
)
@pytest.mark.parametrize("dirty", [None, 1])
def test_stem_snap_write_when_font_not_active_then_refused_before_any_change(
    monkeypatch, current, dirty
):
    backend, package, events = _backend(monkeypatch, dirty=dirty, current=current)
    with pytest.raises(UnsupportedCapability) as error:
        backend.set_info_many({"postscriptStemSnapV": [120], "familyName": "No"})
    assert error.value.capability == "info.postscriptStemSnap.history"
    assert "not the active document" in str(error.value)
    assert "Activate the font first" in str(error.value)
    assert events == [], "no history probe, checkpoint or notify may run"
    assert package.info.postscriptStemSnapV == [90]
    assert package.info.familyName == "Fam", "the whole batch must be refused"


def test_other_info_fields_when_font_not_active_then_written(monkeypatch):
    backend, package, _events = _backend(monkeypatch, dirty=None, current=OTHER)
    backend.set_info_many({"familyName": "New"})
    assert package.info.familyName == "New", "only stem snaps need the active font"


def test_capability_is_named_for_ui_clients():
    entry = NATIVE_CAPABILITIES["info.postscriptStemSnap.history"]
    assert entry["supported"] is False and "Undo" in entry["reason"]


class _OrderBackend:
    """Record the order of native import writes."""

    def __init__(self):
        self.calls = []

    def default_layer(self):
        return "public.default"

    def layer_names(self):
        return ["public.default"]

    def new_glyph(self, name, layer):
        self.calls.append(("new", name))

    def write_glyph(self, name, layer, glyph):
        self.calls.append(("glyph", name))

    def set_info_many(self, values, **kwargs):
        self.calls.append(("info", tuple(sorted(values))))

    def __getattr__(self, name):
        if name.startswith("set_"):
            return lambda *args, **kwargs: self.calls.append((name,))
        raise AttributeError(name)


class _Font:
    def refresh(self):
        pass


def _stemmed_source():
    from ufoLib2 import Font

    source = Font()
    source.newGlyph("a").width = 500
    source.info.familyName = "Order"
    source.info.postscriptStemSnapV = [80]
    source.info.postscriptStemSnapH = [70]
    return source


def test_native_import_writes_stem_snaps_before_any_glyph_edit():
    from fontlab_fontport.interchange import _apply_import

    backend = _OrderBackend()
    events = list(_apply_import(_stemmed_source(), backend, _Font(), True))
    assert backend.calls[0] == (
        "info",
        ("postscriptStemSnapH", "postscriptStemSnapV"),
    ), backend.calls
    assert ("info", ("familyName",)) in backend.calls[
        backend.calls.index(("glyph", "a")) :
    ]
    assert [event["kind"] for event in events].count("info") == 1


def test_ufo_import_keeps_stem_snaps_with_other_info_after_glyphs():
    from fontlab_fontport.interchange import _apply_import

    backend = _OrderBackend()
    list(_apply_import(_stemmed_source(), backend, _Font(), False))
    info = [call for call in backend.calls if call[0] == "info"]
    assert info == [
        ("info", ("familyName", "postscriptStemSnapH", "postscriptStemSnapV"))
    ]
    assert backend.calls.index(("glyph", "a")) < backend.calls.index(info[0])
