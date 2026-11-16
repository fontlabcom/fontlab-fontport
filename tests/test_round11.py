# this_file: tests/test_round11.py
"""Review regressions, exercised without FontLab or a namespace substitute."""

import unittest

import pytest
from fontTools.pens.recordingPen import RecordingPointPen

from fontlab_fontport.errors import StaleObjectError, UnsupportedCapability
from fontlab_fontport.live import RFont
from fontlab_fontport.memory import UFOBackend
from fontlab_fontport.testing import ObjectGenerator, run_test


def test_invalidate_stales_held_glyph_and_is_safe_after_close():
    backend = UFOBackend()
    font = RFont(backend)
    glyph = font.newGlyph("A")
    font.invalidate()
    with pytest.raises(StaleObjectError):
        _ = glyph.width
    assert font["A"].width == 0
    backend.close()
    font.invalidate()
    assert isinstance(font.capabilities(), dict)


def test_adapter_identity_and_scratch_storage():
    font = RFont(UFOBackend())
    for obj in (
        font,
        font.defaultLayer,
        font.kerning,
        font.groups,
        font.features,
        font.lib,
    ):
        assert obj.naked() is obj._naked
        assert obj == obj and obj in [obj] and hash(obj) == hash(obj)
        obj.tempLib["scratch"] = [1]
        assert obj.tempLib["scratch"] == [1]
    assert font.tempLib.font is font
    assert "scratch" not in font.lib


def test_only_named_capabilities_are_classified_and_fixture_routes_reset():
    class Bare(unittest.TestCase):
        def runTest(self):
            raise NotImplementedError("adapter defect")

    class Named(unittest.TestCase):
        def runTest(self):
            raise UnsupportedCapability("test.named", "expected")

    generator = ObjectGenerator(backend_factory=UFOBackend)
    generator.families.append({"family": "stale"})
    assert run_test(Bare(), generator)["status"] == "unclassified"
    row = run_test(Named(), generator)
    assert row["status"] == "UnsupportedCapability" and row["fixtures"] == []


def test_bulk_pen_checks_native_liveness_once_per_entry():
    class Counting(UFOBackend):
        calls = 0

        def check_open(self):
            self.calls += 1
            return super().check_open()

    backend = Counting()
    font = RFont(backend)
    glyph = font.newGlyph("A")
    pen = glyph.getPen()
    pen.moveTo((0, 0))
    for i in range(30):
        pen.lineTo((i, i % 3))
    pen.closePath()
    backend.calls = 0
    glyph.drawPoints(RecordingPointPen())
    first_calls = backend.calls
    assert (
        first_calls <= 3
    )  # owner, layer and glyph existence, independent of point count
    backend.calls = 0
    glyph.drawPoints(RecordingPointPen())
    assert backend.calls == first_calls
    backend.close()
    with pytest.raises(StaleObjectError):
        glyph.drawPoints(RecordingPointPen())


def test_default_save_accepts_unmodified_unicode_and_legacy_baseline(
    monkeypatch, tmp_path
):
    import sys
    from types import SimpleNamespace

    from fontlab_fontport.host import NativeFontBackend

    backend = NativeFontBackend.__new__(NativeFontBackend)
    backend.font_id = 7
    backend._package = lambda: SimpleNamespace(fgPackage=[SimpleNamespace(name="Ω")])
    destination = tmp_path / "baseline.vfj"
    calls = []

    def call(name, **kwargs):
        calls.append((name, kwargs))
        destination.write_text("owned save")

    monkeypatch.setitem(sys.modules, "fontpr", SimpleNamespace(call=call))
    backend.save(str(destination))
    assert calls == [
        ("save_font", {"font_id": 7, "path": str(destination), "overwrite": True})
    ]
    assert destination.read_text() == "owned save"
