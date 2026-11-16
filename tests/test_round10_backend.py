# this_file: tests/test_round10_backend.py
"""Boundary contracts exercised with real UFO/FontParts/defcon objects."""

import importlib
import runpy
from pathlib import Path

import pytest
from fontTools.ufoLib import UFOReader

from fontlab_fontport.errors import StaleObjectError, UnsupportedCapability
from fontlab_fontport.live import RFont
from fontlab_fontport.memory import UFOBackend


def test_ufo_backend_save_respects_structure_and_format(tmp_path):
    font = RFont(UFOBackend())
    font.newGlyph("A").width = 600
    with pytest.raises(UnsupportedCapability, match="UFO 3"):
        font.save(str(tmp_path / "2.ufo"), formatVersion=2)
    for version, structure in ((3, "package"), (3, "zip")):
        path = tmp_path / f"{version}.ufo"
        font.save(str(path), formatVersion=version, fileStructure=structure)
        with UFOReader(path) as reader:
            assert reader.formatVersionTuple.value[0] == version
            assert reader.fileStructure.value == structure


def test_font_copy_refuses_a_native_document_allocation():
    font = RFont(UFOBackend())
    with pytest.raises(UnsupportedCapability, match=r"font.copy"):
        font.copy()


def test_rename_and_layers_are_explicit_backend_operations():
    backend = UFOBackend()
    font = RFont(backend)
    glyph = font.newGlyph("A")
    glyph.name = "B"
    assert glyph is font["B"] and "A" not in font
    glyph.width = 400
    assert backend.font["B"].width == 400
    layer = font.newLayer("background")
    layer.newGlyph("B").width = 500
    layer.name = "sketch"
    assert font.getLayer("sketch")["B"].width == 500
    font.removeLayer("sketch")
    with pytest.raises(StaleObjectError):
        layer.keys()


def test_closed_backend_is_checked_on_cached_glyph_reads():
    backend = UFOBackend()
    font = RFont(backend)
    glyph = font.newGlyph("A")
    pen = glyph.getPen()
    pen.moveTo((0, 0))
    pen.lineTo((100, 0))
    pen.lineTo((0, 100))
    pen.closePath()
    point = glyph[0].points[0]
    lib = glyph.lib
    info = font.info
    groups = font.groups
    kerning = font.kerning
    features = font.features
    layer = font.defaultLayer
    backend.close()
    for read in (
        lambda: font.info,
        lambda: glyph.width,
        lambda: point.x,
        lambda: glyph.name,
        lambda: font.defaultLayer,
        lambda: lib.keys(),
        lambda: lib.naked(),
        lambda: info.font,
        lambda: groups.font,
        lambda: kerning.font,
        lambda: features.font,
        lambda: layer.name,
        lambda: glyph.naked(),
        lambda: font.naked(),
    ):
        with pytest.raises(StaleObjectError):
            read()


def test_persistent_registration_and_launcher_are_opt_in(tmp_path):
    from fontParts import world
    from test_world import Host

    from fontlab_fontport.deploy import write_launcher
    from fontlab_fontport.world import FontWorld, register, unregister

    previous = dict(world.dispatcher._registry)
    env = FontWorld(Host())
    registration = register(env)
    try:
        assert world.CurrentFont() is env.CurrentFont()
        with pytest.raises(UnsupportedCapability, match=r"world.selection"):
            world.CurrentGlyph()
    finally:
        unregister()
    assert world.dispatcher._registry == previous and not registration.active
    target = tmp_path / "fontparts.py"
    assert write_launcher(target) == target
    compile(target.read_text(), str(target), "exec")
    with pytest.raises(FileExistsError):
        write_launcher(target)
    with pytest.raises(ValueError, match="absolute"):
        write_launcher("relative.py")


def test_staged_glyph_edit_commits_once_and_rolls_back_on_body_error():
    from test_live import Backend

    backend = Backend()
    font = RFont(backend)
    with font.edit_glyph("A") as glyph:
        glyph.width = 620
        pen = glyph.getPen()
        pen.moveTo((0, 0))
        pen.lineTo((20, 0))
        pen.lineTo((20, 20))
        pen.closePath()
    assert backend.writes == [("A", "public.default")]
    assert font["A"].width == 620
    with pytest.raises(ValueError, match="reject"), font.edit_glyph("A") as glyph:
        glyph.width = 999
        raise ValueError("reject")
    assert font["A"].width == 620 and len(backend.writes) == 1


def test_pen_when_fractional_points_written_to_memory_backend_then_read_back_exactly():
    """Report 29b: the pen and the commit must not round; memory-backend parity for the native recheck."""
    backend = UFOBackend()
    font = RFont(backend)
    font.newGlyph("A")
    expected = [(10.4, 410.6), (100.25, 410.6), (10.4, 0.75)]
    with font.edit_glyph("A") as glyph:
        pen = glyph.getPen()
        pen.moveTo(expected[0])
        pen.lineTo(expected[1])
        pen.lineTo(expected[2])
        pen.closePath()
        assert [(p.x, p.y) for p in glyph[0].points] == expected
    stored = backend.read_glyph("A", "public.default")
    assert [(p.x, p.y) for c in stored.contours for p in c.points] == expected


@pytest.mark.parametrize("checked_source", [False, True])
def test_launcher_when_executed_then_real_fly_identity_and_registration_handle(
    tmp_path, monkeypatch, checked_source
):
    from test_world import Host

    from fontlab_fontport.deploy import write_launcher
    from fontlab_fontport.world import FontWorld, register

    monkeypatch.syspath_prepend(str(tmp_path))
    canonical = importlib.import_module("fontlab_fontport")
    canonical_world = importlib.import_module("fontlab_fontport.world")
    assert importlib.import_module("fly.fp") is canonical
    assert importlib.import_module("fly.fp.world") is canonical_world
    environment = FontWorld(Host())
    monkeypatch.setattr(canonical_world, "register", lambda: register(environment))
    source = Path(canonical.__file__).resolve().parents[1] if checked_source else None
    target = write_launcher(tmp_path / "startup.py", source=source)
    namespace = runpy.run_path(str(target))
    registration = namespace["fontport_registration"]
    try:
        assert namespace["fontlab_fontport"] is canonical
        assert registration.active
    finally:
        registration.close()
    assert not registration.active


def test_launcher_when_other_source_loaded_then_refuses_before_registration(
    tmp_path, monkeypatch
):
    from fontlab_fontport.deploy import write_launcher

    monkeypatch.syspath_prepend(str(tmp_path))
    world = importlib.import_module("fontlab_fontport.world")
    calls = []
    monkeypatch.setattr(world, "register", lambda: calls.append(True))
    target = write_launcher(tmp_path / "startup.py", source=tmp_path)
    with pytest.raises(RuntimeError, match="different Fontport is already loaded"):
        runpy.run_path(str(target))
    assert calls == []
    with pytest.raises(FileNotFoundError):
        write_launcher(tmp_path / "missing.py", source=tmp_path / "absent")
    assert not (tmp_path / "missing.py").exists()
