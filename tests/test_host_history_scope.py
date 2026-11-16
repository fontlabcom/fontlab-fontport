# this_file: tests/test_host_history_scope.py
"""Native-shaped canvas controls exercising App's real history guard."""

import sys
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace as NS

import pytest
from ufoLib2.objects import Glyph

import fontlab_fontport.host as host
from fontlab_fontport.errors import UnsupportedCapability


class NativeGlyph(NS):
    """Model the measured fresh-note mirror loss on flGlyph.fgGlyph reads."""

    @property
    def fgGlyph(self):
        self.record.lib.pop("note", None)
        self.destructive_reads += 1
        return self.record


class NativeFont(NS):
    """FontGate's name lookup returns a font-owned record, or None."""

    def __getitem__(self, name):
        return next((g for g in self.glyphs if g.name == name), None)

    def keys(self):
        return [g.name for g in self.glyphs]


@pytest.fixture
def scene(monkeypatch):
    events = []
    package = NS(
        id=1,
        fgId=11,
        isNull=False,
        masters=["Regular"],
        checkInitHistoryState=lambda _: events.append("history"),
    )
    target = NS(advanceWidth=500, anchors=[], isNull=False)
    glyph = NativeGlyph(
        name="D",
        fgGlyphId=21,
        record=NS(id=21, name="D", unicodes=[], lib={}),
        destructive_reads=0,
        package=package,
        isNull=False,
        findLayer=lambda _: None,
        addLayer=lambda _: events.append("add"),
        removeLayer=lambda _: events.append("remove"),
    )
    package.fgPackage = NativeFont(id=11, glyphs=[glyph.record])
    shown = NS(name="C", package=package, isNull=False)
    canvas = NS(
        isNull=False,
        textBlocks=[NS(glyphsCount=lambda: 1, getGlyphAt=lambda _: NS(glyph=shown))],
    )
    workspace = NS(getActiveCanvas=lambda: canvas, currentPackage=package)
    native = NS(
        flWorkspace=NS(instance=lambda: workspace),
        CurrentGlyph=lambda: shown,
        flLayer=lambda name: NS(name=name),
        flItems=NS(notifyChangesApplied=lambda *a: events.append("notify")),
    )
    monkeypatch.setitem(sys.modules, "fontlab", native)
    monkeypatch.setitem(sys.modules, "fontgate", NS(fgGlyph=lambda: object()))
    monkeypatch.setitem(sys.modules, "PythonQt", NS(QtCore=object()))
    monkeypatch.setitem(
        sys.modules, "fontpr", NS(call=lambda *a, **k: events.append("create"))
    )
    monkeypatch.setattr(host, "write_glyph", lambda *a: None)
    backend = host.NativeFontBackend.__new__(host.NativeFontBackend)
    backend.font_id = 11  # native font ids are fgId (verified 2026-11-03)
    backend._package = lambda: package
    backend._target = lambda *a: (package, glyph, target)
    backend.read_glyph = lambda *a: Glyph("D", width=500)
    backend._stage_shapes = lambda *a: []
    backend.layer_names = lambda: ("Regular", "aux")
    package.findName = lambda _: glyph
    return NS(
        backend=backend,
        glyph=glyph,
        shown=shown,
        workspace=workspace,
        package=package,
        target=target,
        events=events,
    )


def act(s, action):
    if action == "write":
        s.backend.write_glyph_named("D", "aux", Glyph("D", width=600))
    elif action == "add":
        s.backend.new_glyph("D", "aux")
    elif action == "remove":
        s.backend.remove_glyph("D", "aux")
    else:
        s.package.findName = lambda _: None
        s.backend.new_glyph("new", "Regular")


@pytest.mark.parametrize("action", ["write", "add", "remove", "create"])
def test_off_canvas_refuses_before_bound_write_or_history(scene, action):
    with pytest.raises(ValueError, match="Glyph window"):
        act(scene, action)
    assert scene.events == [], "Refusal must precede history and native mutation"
    assert scene.target.advanceWidth == 500, "Refusal changed bound width"


@pytest.mark.parametrize("action", ["write", "add", "remove", "create"])
def test_font_window_allows_existing_paths(scene, action):
    scene.workspace.getActiveCanvas = lambda: None
    act(scene, action)
    assert scene.events, "Permitted operation did not reach its native path"


@pytest.mark.parametrize("action", ["write", "add", "remove"])
def test_canvas_owner_is_allowed(scene, action):
    scene.glyph.name = "C"
    act(scene, action)
    assert scene.events, "Canvas-owned operation was blocked"


def test_same_name_other_package_is_refused(scene):
    scene.glyph.name = "C"
    scene.glyph.package = NS(id=2)
    with pytest.raises(ValueError, match="Glyph window"):
        act(scene, "write")
    assert not scene.events, "Another package reached history"


def test_noop_returns_without_history_even_off_canvas(scene):
    scene.backend.write_glyph_named("D", "aux", Glyph("D", width=500))
    assert not scene.events, "No-op enrolled history"


@pytest.mark.parametrize("current", [True, False])
def test_unreadable_canvas_uses_current_glyph_fallback(scene, current):
    def unreadable():
        raise RuntimeError("unreadable canvas")

    scene.workspace.getActiveCanvas = unreadable
    scene.glyph.name = "C" if current else "D"
    if current:
        act(scene, "write")
        assert scene.events, "Current glyph fallback was blocked"
    else:
        with pytest.raises(ValueError, match="Glyph window"):
            act(scene, "write")
        assert not scene.events, "Unreadable canvas allowed another owner"


def test_validation_and_master_refusals_precede_canvas(scene):
    with pytest.raises(ValueError, match="nonempty"):
        scene.backend.new_glyph("", "aux")
    with pytest.raises(KeyError):
        scene.backend.new_glyph("D", "unknown")
    scene.glyph.findLayer = lambda _: scene.target
    with pytest.raises(ValueError, match="already exists"):
        scene.backend.new_glyph("D", "aux")
    with pytest.raises(UnsupportedCapability, match=r"glyph\.delete\.master"):
        scene.backend.remove_glyph("D", "Regular")
    assert not scene.events, "Invalid input reached mutation"


def test_off_thread_refuses_even_without_canvas(scene):
    scene.workspace.getActiveCanvas = lambda: None
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(act, scene, "write")
        with pytest.raises(ValueError, match="Glyph window"):
            future.result()
    assert not scene.events, "Worker thread reached mutation"


def test_invalid_source_precedes_canvas_refusal(scene):
    source = Glyph("D", width=600)
    source.appendAnchor(dict(name="top", x=0.5, y=700))
    with pytest.raises(UnsupportedCapability):
        scene.backend.write_glyph_named("D", "aux", source)
    assert not scene.events, "Invalid source enrolled history"


def test_unreadable_canvas_refuses_new_identity(scene):
    def unreadable():
        raise RuntimeError("unreadable canvas")

    scene.workspace.getActiveCanvas = unreadable
    with pytest.raises(ValueError, match="Glyph window"):
        act(scene, "create")
    assert not scene.events, "Unreadable canvas allowed creation"


def test_host_import_keeps_native_and_shared_guard_lazy():
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import sys; import fontlab_fontport.host; "
            "assert not {'fontlab', 'fontgate', 'PythonQt', 'fontlabapp.core.edit_guards'} & sys.modules.keys()",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("hint", ["hasHints", "hasTTData", "hasTTH"])
def test_hinted_geometry_refuses_before_history(scene, monkeypatch, hint):
    monkeypatch.setitem(sys.modules, "PythonQt", NS(QtCore=object(), QtGui=object()))
    scene.target.hasHints = scene.target.hasTTData = scene.target.hasTTH = False
    setattr(scene.target, hint, True)
    with pytest.raises(UnsupportedCapability, match="hinted"):
        host.NativeFontBackend._stage_shapes(
            scene.package, scene.target, NS(layer=None), Glyph("D"), True
        )
    assert not scene.events, "Hint refusal reached history"


def test_layer_lookup_reacquires_and_refuses_missing_handles(scene):
    backend = scene.backend
    del backend._target
    scene.glyph.findLayer = lambda _: scene.target
    assert backend._target("D", "aux")[1] is scene.glyph
    backend.check_glyph("D", "aux")
    scene.glyph.findLayer = lambda _: None
    with pytest.raises(KeyError):
        backend._target("D", "aux")
    from fontlab_fontport.errors import StaleObjectError

    with pytest.raises(StaleObjectError):
        backend.check_glyph("D", "aux")
    scene.package.findName = lambda _: None
    with pytest.raises(KeyError):
        backend._target("missing", "aux")


def test_layer_discovery_and_glyph_membership(scene):
    backend = scene.backend
    del backend.layer_names
    scene.package.defaultMaster = "Regular"
    scene.package.fgPackage = [NS(name="D")]
    scene.glyph.layers = [NS(name="Regular"), NS(name="aux")]
    scene.glyph.findLayer = lambda name: scene.target if name == "aux" else None
    assert backend.layer_names() == ("Regular", "aux"), "Layer union changed"
    assert backend.has_layer("Regular") and backend.has_layer("aux")
    assert not backend.has_layer("missing")
    assert backend.default_layer() == "Regular"
    assert backend.glyph_names("aux") == ("D",)
    assert backend.glyph_names("Regular") == ()
    with pytest.raises(KeyError):
        backend.glyph_names("missing")


@pytest.mark.parametrize(
    "method,args",
    [
        ("rename_glyph", ("D", "E", "aux")),
        ("new_layer", ("new",)),
        ("remove_layer", ("aux",)),
        ("rename_layer", ("aux", "new")),
    ],
)
def test_unqualified_topology_operations_remain_refused(scene, method, args):
    with pytest.raises(UnsupportedCapability):
        getattr(scene.backend, method)(*args)
    assert not scene.events, "Unsupported topology operation mutated the host"


def test_write_metadata_and_anchors_preserves_active_layer_note(scene, monkeypatch):
    scene.glyph.name = "C"
    scene.glyph.activeLayer = NS(note="layer note")
    scene.glyph.record.name = "C"
    scene.glyph.lib = {}
    scene.glyph.note = ""
    scene.target.removeAnchor = lambda pin: scene.target.anchors.remove(pin)
    scene.target.addAnchor = lambda pin: scene.target.anchors.append(pin)
    scene.target.anchors = [NS(name="old")]
    monkeypatch.setitem(
        sys.modules, "PythonQt", NS(QtCore=NS(QPointF=lambda x, y: (x, y)))
    )
    monkeypatch.setattr(
        sys.modules["fontlab"],
        "flPinPoint",
        lambda point: NS(point=point),
        raising=False,
    )
    source = Glyph(
        "D", width=600, height=900, unicodes=[68], lib={"a": 1}, note="new note"
    )
    source.appendAnchor(dict(name="top", x=10, y=700))
    scene.backend.write_glyph_named("D", "aux", source)
    assert (
        scene.glyph.note == "new note" and scene.glyph.activeLayer.note == "layer note"
    )
    assert scene.glyph.record.unicodes == [68] and scene.glyph.lib == {"a": 1}
    assert scene.target.advanceHeight == 900 and scene.target.anchors[0].name == "top"
    assert scene.events == ["history", "notify", "notify"], (
        "Checkpoint protocol changed"
    )


@pytest.mark.parametrize(
    "error",
    [
        UnsupportedCapability("glyph.geometry", "unsupported"),
        NotImplementedError("unsupported"),
    ],
)
def test_geometry_staging_refusal_keeps_history_untouched(scene, error):
    def fail(*args):
        raise error

    scene.backend._stage_shapes = fail
    with pytest.raises(UnsupportedCapability, match="unsupported"):
        act(scene, "write")
    assert not scene.events, "Staging failure enrolled history"


def test_read_snapshot_applies_native_transforms_and_global_note(scene, monkeypatch):
    from test_pens import NativeGlyph

    matrix = NS(
        m11=lambda: 1,
        m12=lambda: 0,
        m21=lambda: 0,
        m22=lambda: 1,
        dx=lambda: 10,
        dy=lambda: 20,
    )
    component = NS(
        isComponent=True, transform=matrix, shapeData=NS(componentGlyph="base")
    )
    native = NativeGlyph()
    from test_pens import NATIVE

    from fontlab_fontport.pens import FontGatePointPen

    pen = FontGatePointPen(native, native=NATIVE)
    pen.beginPath()
    pen.addPoint((0, 0), "move")
    pen.addPoint((100, 0), "line")
    pen.endPath()
    outline = NS(isComponent=False, convertToFgShape=lambda result: None)
    fg_shape = NS(
        matrix=NS(asTuple=lambda: (1, 0, 0, 1, 0, 0)),
        contours=native.layer.shapes[0].contours,
    )
    monkeypatch.setattr(
        sys.modules["fontgate"], "fgShape", lambda: fg_shape, raising=False
    )
    scene.target.transform = matrix
    scene.target.shapes = [component, outline]
    scene.target.advanceHeight = 0
    scene.target.anchors = [NS(name="top", point=NS(x=lambda: 50, y=lambda: 700))]
    scene.glyph.lib = {"key": 1}
    scene.glyph.activeLayer = NS(note="layer")
    scene.glyph.record.unicodes = [68]
    monkeypatch.setattr(
        sys.modules["fontpr"], "call", lambda *a, **k: {"note": "global"}
    )
    del scene.backend.read_glyph
    snapshot = scene.backend.read_glyph("D", "aux")
    assert snapshot.note == "global" and snapshot.width == 500
    assert snapshot.components[0].transformation[-2:] == (20, 40), (
        "Component transform was not composed"
    )
    assert snapshot.contours[0].points[0].x == 10, "Outline transform was lost"
    assert snapshot.anchors[0].name == "top"
    scene.glyph.activeLayer = None
    scene.glyph.note = "direct"
    assert scene.backend._glyph_note(scene.glyph) == "direct"
    scene.glyph.activeLayer = NS(note="")
    assert scene.backend._glyph_note(scene.glyph) == "direct"


@pytest.fixture
def note_scene(scene):
    """Use actual backend lookup/read methods and two distinct registered fonts."""
    scene.backend._closed = False
    del scene.backend._package, scene.backend._target, scene.backend.read_glyph
    scene.glyph.lib = {"nested": {"value": [1, "kept"]}}
    scene.glyph.note = "fresh global note"
    scene.glyph.activeLayer = NS(note="")
    scene.glyph.record.lib = {"note": "fresh global note", "private": [3, 4]}
    scene.glyph.record.unicodes = [68]
    scene.glyph.findLayer = lambda _: scene.target
    scene.target.advanceHeight = 0
    scene.target.shapes = []
    scene.target.transform = NS(
        m11=lambda: 1,
        m12=lambda: 0,
        m21=lambda: 0,
        m22=lambda: 1,
        dx=lambda: 0,
        dy=lambda: 0,
    )
    scene.other_record = NS(id=31, name="D", unicodes=[913], lib={"note": "other"})
    scene.other = NS(
        id=2, fgId=12, fgPackage=NativeFont(id=12, glyphs=[scene.other_record])
    )
    scene.workspace.currentPackage = scene.other
    scene.workspace.findPackageId = lambda key: {11: scene.package, 12: scene.other}.get(
        key
    )
    return scene


@pytest.mark.parametrize("unicodes", [[], [0], [68, 0x1F642]])
def test_read_when_target_is_noncurrent_preserves_exact_notes_and_lib(
    note_scene, unicodes
):
    import copy

    s = note_scene
    s.glyph.record.unicodes = list(unicodes)
    before = copy.deepcopy((s.glyph.lib, s.glyph.record.lib, s.other_record.__dict__))
    snapshot = s.backend.read_glyph("D", "aux")
    assert snapshot.unicodes == unicodes, "Read Unicode from the other/current font"
    assert snapshot.note == "fresh global note", "Global note was lost"
    assert (s.glyph.lib, s.glyph.record.lib, s.other_record.__dict__) == before, (
        "Read changed the exact note/lib payload"
    )
    assert s.glyph.destructive_reads == 0, "Read exported through destructive fgGlyph"
    snapshot.lib["nested"]["value"].append("detached")
    assert s.glyph.lib == before[0], "Snapshot retained the native lib container"
    assert not s.events, "Read entered history"


@pytest.mark.parametrize("unicodes", [[], [0], [69, 0x1F642]])
def test_unicode_write_when_target_is_noncurrent_preserves_note_mirror(
    note_scene, unicodes
):
    s = note_scene
    s.workspace.getActiveCanvas = lambda: None
    source = Glyph(
        "D", width=500, unicodes=unicodes, note=s.glyph.note, lib=s.glyph.lib
    )
    s.backend.write_glyph_named("D", "aux", source)
    assert s.glyph.record.unicodes == unicodes, "Unicode write missed target"
    assert s.other_record.unicodes == [913], "Unicode write changed current font"
    assert s.glyph.record.lib == {"note": "fresh global note", "private": [3, 4]}, (
        "Unicode write removed an unrelated note/lib field"
    )
    assert s.glyph.note == "fresh global note" and s.glyph.activeLayer.note == ""
    assert s.glyph.destructive_reads == 0, "Writer exported through destructive fgGlyph"
    assert s.events == ["history", "notify", "notify"], "History protocol changed"


@pytest.mark.parametrize("changing", [False, True])
def test_noop_and_off_canvas_refusal_preserve_note_mirror(note_scene, changing):
    s = note_scene
    source = Glyph(
        "D",
        width=600 if changing else 500,
        unicodes=[68],
        note=s.glyph.note,
        lib=s.glyph.lib,
    )
    if changing:
        with pytest.raises(ValueError, match="Glyph window"):
            s.backend.write_glyph_named("D", "aux", source)
    else:
        s.backend.write_glyph_named("D", "aux", source)
    assert s.glyph.record.lib == {"note": "fresh global note", "private": [3, 4]}, (
        "Preflight changed the note/lib mirror before no-op/refusal"
    )
    assert not s.events, "No-op/refusal entered history"


@pytest.mark.parametrize("missing", ["package", "glyph", "layer"])
def test_missing_registered_binding_keeps_existing_errors(note_scene, missing):
    s = note_scene
    if missing == "package":
        s.workspace.findPackageId = lambda _: None
    elif missing == "glyph":
        s.package.findName = lambda _: None
    else:
        s.glyph.findLayer = lambda _: None
    expected = host.StaleObjectError if missing == "package" else KeyError
    with pytest.raises(expected):
        s.backend.read_glyph("D", "aux")
    assert not s.events and s.glyph.destructive_reads == 0


@pytest.mark.parametrize(
    "stale",
    ["package", "owner", "font", "no_font", "missing", "name", "glyph", "duplicate"],
)
def test_stale_registered_record_refuses_without_fallback_or_history(note_scene, stale):
    s = note_scene
    if stale == "package":
        s.package.fgId = 12
    elif stale == "owner":
        s.glyph.package = s.other
    elif stale == "font":
        s.package.fgPackage.id = 12
    elif stale == "no_font":
        s.package.fgPackage = None
    elif stale == "missing":
        s.package.fgPackage.glyphs = []
    elif stale == "name":
        s.package.fgPackage.__class__ = type(
            "WrongName",
            (NativeFont,),
            {
                "__getitem__": lambda self, name: s.other_record,
            },
        )
        s.other_record.name = "other"
    elif stale == "duplicate":
        s.package.fgPackage.glyphs.insert(0, s.other_record)
    else:
        s.glyph.record.id = 31
    with pytest.raises(host.StaleObjectError):
        s.backend.read_glyph("D", "aux")
    assert not s.events and s.glyph.destructive_reads == 0
    assert s.other_record.unicodes == [913], "Stale lookup used another font"


@pytest.mark.parametrize(
    "duplicate_index", [0, 1], ids=["other-first", "expected-first"]
)
@pytest.mark.parametrize("operation", ["read", "write"])
def test_duplicate_owner_refuses_in_either_order_before_history(
    note_scene, duplicate_index, operation
):
    s = note_scene
    s.workspace.getActiveCanvas = lambda: None
    s.package.fgPackage.glyphs.insert(duplicate_index, s.other_record)
    with pytest.raises(host.StaleObjectError):
        if operation == "read":
            s.backend.read_glyph("D", "aux")
        else:
            s.backend.write_glyph_named("D", "aux", Glyph("D", unicodes=[69]))
    assert not s.events, "Ambiguous owner reached history or mutation"
    assert s.glyph.destructive_reads == 0, "Ambiguity check exported glyph data"
    assert s.glyph.record.unicodes == [68], "Ambiguity check changed Unicode values"
    assert s.glyph.record.lib == {"note": "fresh global note", "private": [3, 4]}
    assert s.other_record.unicodes == [913], "Ambiguity check changed the other record"


def test_invalid_unicode_source_refuses_before_registered_read(note_scene):
    s = note_scene
    source = Glyph("D", width=600, unicodes=[68], note=s.glyph.note, lib=s.glyph.lib)
    source.appendAnchor(dict(name="top", x=0.5, y=700))
    with pytest.raises(UnsupportedCapability, match="fractional"):
        s.backend.write_glyph_named("D", "aux", source)
    assert s.glyph.record.lib == {"note": "fresh global note", "private": [3, 4]}
    assert not s.events and s.glyph.destructive_reads == 0
