# this_file: tests/test_export.py
"""Real UFO/TTF artifacts, component closure and no-overwrite guarantees."""


import pytest
from fontTools.ttLib import TTFont
from ufoLib2 import Font
from ufoLib2.objects import Component, Glyph

from fontlab_fontport.export import compile_ttf, export_ufo_subset


class Backend:
    def __init__(self):
        a = Glyph(name="A", width=500, unicodes=[65])
        pen = a.getPointPen()
        pen.beginPath()
        for point in ((10, 0), (210, 0), (110, 700)):
            pen.addPoint(point, segmentType="line")
        pen.endPath()
        accented = Glyph(name="Aacute", width=500, unicodes=[193])
        accented.components.append(Component(baseGlyph="A"))
        self.glyphs = {"A": a, "Aacute": accented}

    def default_layer(self):
        return "Regular"

    def glyph_names(self, layer):
        return tuple(self.glyphs)

    def read_glyph(self, name, layer):
        return self.glyphs[name]

    def get_info(self, name):
        return {"unitsPerEm": 1000, "copyright": "Original author"}[name]


def export(backend, destination):
    return export_ufo_subset(backend, ["Aacute"], destination,
                             family_name="Owned Scripting Sample", license_text="CC0",
                             source_url="https://code.fontlab.com/getgo-fonts/plum-var/")


def test_subset_reopens_with_components_metadata_and_unchanged_source(tmp_path):
    backend = Backend()
    target = tmp_path / "sample.ufo"
    export(backend, target)
    with Font.open(target) as font:
        assert set(font.keys()) == {"A", "Aacute"}
        assert font["Aacute"].components[0].baseGlyph == "A"
        assert font.info.copyright == "Original author"
        assert font.info.openTypeNameLicense == "CC0"
        assert font.info.familyName == "Owned Scripting Sample"
        assert font.lib["org.fontlab.fontport.sourceURL"].startswith("https://code.fontlab.com/")
    assert backend.glyphs["A"].width == 500 and len(backend.glyphs["A"].contours) == 1


def test_real_compiler_writes_readable_ttf_with_unicode_and_advance(tmp_path):
    pytest.importorskip("ufo2ft")
    source, target = tmp_path / "sample.ufo", tmp_path / "sample.ttf"
    export(Backend(), source)
    compile_ttf(source, target)
    with TTFont(target) as font:
        assert font.getBestCmap()[193] == "Aacute"
        assert font["hmtx"]["A"][0] == 500
        assert font["glyf"]["A"].numberOfContours == 1
        assert font["name"].getDebugName(13) == "CC0"


def test_cycle_and_unknown_glyph_fail_before_any_output(tmp_path):
    backend = Backend()
    backend.glyphs["A"].components.append(Component(baseGlyph="Aacute"))
    with pytest.raises(ValueError, match="Cyclic"):
        export(backend, tmp_path / "cycle.ufo")
    assert not (tmp_path / "cycle.ufo").exists()
    with pytest.raises(KeyError):
        export_ufo_subset(backend, ["missing"], tmp_path / "missing.ufo", family_name="Sample")
    assert not (tmp_path / "missing.ufo").exists()


def test_existing_outputs_and_wrong_suffixes_are_never_overwritten(tmp_path):
    existing = tmp_path / "existing.ufo"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        export(Backend(), existing)
    wrong = tmp_path / "wrong.vfj"
    with pytest.raises(ValueError):
        export(Backend(), wrong)
    target = tmp_path / "existing.ttf"
    target.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        compile_ttf(existing, target)
    assert target.read_bytes() == b"keep"
    with pytest.raises(ValueError):
        compile_ttf(existing, tmp_path / "wrong.otf")


def test_empty_selection_and_bad_family_name_fail_before_output(tmp_path):
    for names, family in (([], "Sample"), (["A"], "  "), ([None], "Sample")):
        with pytest.raises((TypeError, ValueError)):
            export_ufo_subset(Backend(), names, tmp_path / "bad.ufo", family_name=family)
    assert not (tmp_path / "bad.ufo").exists()
