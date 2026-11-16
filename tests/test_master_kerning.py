# this_file: tests/test_master_kerning.py
"""Per-master kerning: native read by master name, export session, designspace."""

from types import SimpleNamespace

from fontTools.designspaceLib import DesignSpaceDocument
from test_designspace_io import two_master_font
from ufoLib2 import Font

from fontlab_fontport.designspace_io import LOSSES, export_designspace
from fontlab_fontport.host import NativeFontBackend
from fontlab_fontport.interchange import ExportSession
from fontlab_fontport.memory import UFOBackend
from fontlab_fontport.native_kerning import read_kerning

KERN = {"Light": -50, "Bold": -80}


def native_pairs(value):
    """Minimal fgKerning double: items() yields (native pair, value)."""
    pair = SimpleNamespace(
        left=SimpleNamespace(id="A", mode="glyphMode"),
        right=SimpleNamespace(id="V", mode="glyphMode"),
    )
    return SimpleNamespace(items=lambda: [(pair, value)], groups={})


def native_package():
    calls = []

    def kerning(*master):
        calls.append(master)
        return native_pairs(KERN[master[0] if master else "Light"])

    package = SimpleNamespace(
        fgPackage=SimpleNamespace(groups={}),
        kerning=kerning,
        masters=("Light", "Bold"),
        defaultMaster="Light",
    )
    return package, calls


def test_read_kerning_when_master_named_then_calls_package_kerning_with_it():
    package, calls = native_package()
    assert read_kerning(package, "Bold") == {("A", "V"): -80}
    assert ("Bold",) in calls, "the accessor is flPackage.kerning(master_name)"
    assert read_kerning(package) == {("A", "V"): -50}
    assert calls[-1] == (), "no master means the current master, as before"


def test_backend_get_master_kerning_when_not_a_master_then_none():
    package, _ = native_package()
    backend = NativeFontBackend.__new__(NativeFontBackend)
    backend._package = lambda: package
    assert backend.get_master_kerning("Bold") == {("A", "V"): -80}
    assert backend.get_master_kerning("Brace {500}") is None


class MasterBackend(UFOBackend):
    """UFOBackend that also reports each master's own kerning."""

    def get_master_kerning(self, name):
        return {("A", "A"): KERN[name]} if name in KERN else None


def test_session_when_backend_has_master_kerning_then_each_master_is_recorded():
    session = ExportSession(MasterBackend(two_master_font()))
    for _ in session.steps():
        pass
    assert session.master_kerning == {
        "Light": {("A", "A"): -50},
        "Bold": {("A", "A"): -80},
    }
    assert session.font.kerning[("public.kern1.A", "A")] == -20, "key master intact"


def test_session_when_backend_has_no_master_reader_then_nothing_recorded():
    session = ExportSession(UFOBackend(two_master_font()))
    for _ in session.steps():
        pass
    assert session.master_kerning == {}


def test_export_when_masters_differ_then_each_ufo_has_its_own_kerning(tmp_path):
    package = SimpleNamespace(
        axes=[
            SimpleNamespace(
                name="Weight",
                shortName="wt",
                tag="wght",
                minimal=100,
                default=100,
                maximum=900,
                map={},
            )
        ],
        masters=("Light", "Bold"),
        location=lambda name: {"wt": {"Light": 100, "Bold": 900}[name]},
        instances=[],
    )
    backend = MasterBackend(two_master_font())
    backend._package = lambda: package
    path, losses = export_designspace(backend, tmp_path / "Demo.designspace")
    for source in DesignSpaceDocument.fromfile(path).sources:
        ufo = Font.open(tmp_path / source.filename)
        assert dict(ufo.kerning) == {("A", "A"): KERN[source.name]}, source.name
        assert ufo.groups["public.kern1.A"] == ["A"], "groups stay shared"
    assert not [x for x in losses if "masterKerning" in x]
    assert any("groups" in x and "shared" in x for x in losses), LOSSES
