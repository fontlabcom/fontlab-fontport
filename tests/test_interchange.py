# this_file: tests/test_interchange.py
"""Whole-font interchange uses real ufoLib2 storage and upstream point pens."""

import pytest
from fontPens.digestPointPen import DigestPointPen
from ufoLib2 import Font

from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.interchange import ExportSession, import_ufo, preflight_import
from fontlab_fontport.memory import UFOBackend


def source_font():
    source = Font()
    source.info.familyName = "Fontport owned"
    source.info.unitsPerEm = 1000
    source.features.text = "languagesystem DFLT dflt;\n"
    source.lib["test"] = {"value": [1, 2]}
    source.groups["public.kern1.A"] = ["A"]
    source.kerning["A", "V"] = -12.5
    a = source.newGlyph("A")
    source.newGlyph("V")
    a.width = 620
    a.appendAnchor({"name": "top", "x": 12.5, "y": 700.25})
    a.appendGuideline({"x": 0, "y": 10, "angle": 0, "name": "baseline"})
    pen = a.getPen()
    pen.moveTo((0, 0))
    pen.lineTo((50, 0))
    pen.lineTo((0, 100))
    pen.closePath()
    source.newGlyph("composite").getPointPen().addComponent("A", (1, 0, 0, 1, 10, 20))
    source.layers.newLayer("background").newGlyph("A").width = 500
    return source


def digest(glyph):
    pen = DigestPointPen()
    glyph.drawPoints(pen)
    return pen.getDigest()


def test_whole_font_export_then_import_keeps_supported_ufo_fields(tmp_path):
    source = source_font()
    export = ExportSession(UFOBackend(source))
    with pytest.raises(RuntimeError, match="Exhaust"):
        export.save(tmp_path / "early.ufo")
    units = list(export.steps())
    path = export.save(tmp_path / "export.ufo")
    with pytest.raises(FileExistsError):
        export.save(path)
    with Font.open(path) as reopened:
        assert len(units) > len(source)
        backend = UFOBackend()
        with import_ufo(reopened, lambda: backend) as (font, steps):
            list(steps)
            assert set(font.keys()) == set(source.keys())
            assert digest(font["A"]) == digest(source["A"])
            assert font["A"].anchors[0].position == (12.5, 700.25)
            assert font["A"].guidelines[0].y == 10
            assert font.getLayer("background")["A"].width == 500
            assert dict(font.kerning) == source.kerning
            assert dict(font.groups) == {k: tuple(v) for k, v in source.groups.items()}
            assert font.features.text == source.features.text
            assert font.lib["test"] == source.lib["test"]
            assert font.info.familyName == source.info.familyName
        assert backend.closed


def test_native_import_unsupported_layers_or_precision_allocates_nothing():
    source = source_font()
    allocations = []
    with (
        pytest.raises(UnsupportedCapability, match=r"ufo.import.layers"),
        import_ufo(source, lambda: allocations.append(True), native=True),
    ):
        pytest.fail("must refuse before allocating")
    assert not allocations
    del source.layers["background"]
    with pytest.raises(UnsupportedCapability, match=r"precision|guidelines"):
        list(preflight_import(source, native=True))


def test_import_closes_owned_backend_after_failed_apply():
    backend = UFOBackend()
    with pytest.raises(ValueError, match="stop"), import_ufo(Font(), lambda: backend):
        raise ValueError("stop")
    assert backend.closed


def test_incremental_import_requires_complete_detached_preflight():
    from fontlab_fontport.interchange import ImportSession

    source = source_font()
    session = ImportSession(source)
    allocations = []

    def create():
        allocations.append(True)
        return UFOBackend()

    with pytest.raises(RuntimeError, match="Exhaust"):
        session.begin(create)
    assert not allocations
    list(session.preflight_steps())
    source["A"].width = 999
    font, steps = session.begin(create)
    try:
        list(steps)
        assert font["A"].width == 620
        with pytest.raises(RuntimeError, match="once"):
            session.begin(create)
        assert len(allocations) == 1
    finally:
        font.close()


def test_foreign_font_lib_refuses_export_without_silently_removing_values():
    source = Font()
    source.lib["foreign"] = None
    export = ExportSession(UFOBackend(source))
    with pytest.raises(UnsupportedCapability, match=r"ufo.export.lib.plist"):
        list(export.steps())
    assert source.lib["foreign"] is None


def test_native_export_reads_heavy_feature_metadata_only_once():
    class NativeCounter(UFOBackend):
        font_id = 1
        reads = 0

        def get_feature_blocks(self):
            self.reads += 1
            return {"prefix": "languagesystem DFLT dflt;\n", "features": []}

        def get_features(self):
            pytest.fail("Do not make a second heavy native metadata call")

    backend = NativeCounter()
    export = ExportSession(backend)
    list(export.steps())
    assert backend.reads == 1
    assert export.font.features.text == "languagesystem DFLT dflt;\n"


def test_native_import_without_language_prefix_refuses_before_allocation():
    source = Font()
    source.features.text = "feature liga { sub A A by V; } liga;\n"
    allocations = []
    with (
        pytest.raises(
            UnsupportedCapability, match=r"ufo.import.features.languagesystem"
        ),
        import_ufo(source, lambda: allocations.append(True), native=True),
    ):
        pytest.fail("Must refuse before allocating a destination")
    assert not allocations


def test_native_preflight_when_kerning_fractional_then_refusal_names_pair_and_value():
    source = Font()
    source.kerning[("A", "V")] = -56.5
    with pytest.raises(UnsupportedCapability) as caught:
        list(preflight_import(source, native=True))
    assert "UFO kerning: A V = -56.5 is not a whole number" in str(caught.value)
    assert "no changes applied" in str(caught.value)
