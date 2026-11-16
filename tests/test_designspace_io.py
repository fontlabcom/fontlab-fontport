# this_file: tests/test_designspace_io.py
"""Designspace export: axes, sources, instances and one UFO per master."""

from types import SimpleNamespace

import pytest
from fontTools.designspaceLib import DesignSpaceDocument
from ufoLib2 import Font
from ufoLib2.objects import Glyph

from fontlab_fontport.designspace_io import (
    LOSSES,
    export_designspace,
    write_designspace,
)
from fontlab_fontport.memory import UFOBackend


def two_master_font():
    font = Font()
    font.info.familyName = "Demo"
    font.info.unitsPerEm = 1000
    font.groups["public.kern1.A"] = ["A"]
    font.kerning[("public.kern1.A", "A")] = -20
    font.lib["demo.key"] = "v"
    font.features.text = "feature liga { sub A A by A; } liga;"
    for layer_name, width in (("Light", 500), ("Bold", 640)):
        layer = font.layers.newLayer(layer_name)
        glyph = Glyph(name="A", width=width)
        glyph.appendAnchor({"name": "top", "x": 250, "y": 700})
        layer.insertGlyph(glyph)
    return font


def document():
    doc = DesignSpaceDocument()
    doc.addAxisDescriptor(
        name="Weight", tag="wght", minimum=100, default=100, maximum=900
    )
    doc.addSourceDescriptor(name="Light", designLocation={"Weight": 100})
    doc.addSourceDescriptor(name="Bold", designLocation={"Weight": 900})
    doc.addInstanceDescriptor(name="Medium", designLocation={"Weight": 500})
    return doc


def test_write_when_two_masters_then_reopened_designspace_matches_ufos(tmp_path):
    font, doc = two_master_font(), document()
    target = write_designspace(font, doc, tmp_path / "Demo.designspace")
    reopened = DesignSpaceDocument.fromfile(target)
    assert [a.tag for a in reopened.axes] == ["wght"]
    assert [i.name for i in reopened.instances] == ["Medium"]
    assert [s.filename for s in reopened.sources] == [
        "Demo-Light.ufo",
        "Demo-Bold.ufo",
    ]
    for source, width in zip(reopened.sources, (500, 640), strict=True):
        ufo = Font.open(tmp_path / source.filename)
        assert ufo["A"].width == width, "each UFO carries its own master's outline"
        assert [a.name for a in ufo["A"].anchors] == ["top"]
        assert ufo.kerning[("public.kern1.A", "A")] == -20
        assert ufo.groups["public.kern1.A"] == ["A"]
        assert ufo.lib["demo.key"] == "v"
        assert "liga" in ufo.features.text
        assert ufo.info.familyName == "Demo"
    assert not doc.sources[0].filename, "the input document is not modified"


@pytest.mark.parametrize("name", ["Demo.txt", "Demo"])
def test_write_when_destination_not_designspace_then_value_error(tmp_path, name):
    with pytest.raises(ValueError, match=r"\.designspace"):
        write_designspace(two_master_font(), document(), tmp_path / name)


def test_write_when_source_has_no_layer_then_refused_and_nothing_written(tmp_path):
    doc = document()
    doc.addSourceDescriptor(name="Black", designLocation={"Weight": 900})
    with pytest.raises(ValueError, match="Black"):
        write_designspace(two_master_font(), doc, tmp_path / "Demo.designspace")
    assert list(tmp_path.iterdir()) == []


def test_write_when_no_sources_then_refused(tmp_path):
    with pytest.raises(ValueError, match="no sources"):
        write_designspace(Font(), DesignSpaceDocument(), tmp_path / "x.designspace")


def test_write_when_existing_file_then_refused_without_overwrite(tmp_path):
    (tmp_path / "Demo-Bold.ufo").mkdir()
    with pytest.raises(FileExistsError):
        write_designspace(two_master_font(), document(), tmp_path / "Demo.designspace")
    assert not (tmp_path / "Demo.designspace").exists()


def test_write_when_names_collide_as_files_then_refused(tmp_path):
    doc = DesignSpaceDocument()
    doc.addAxisDescriptor(name="Weight", tag="wght", minimum=1, default=1, maximum=9)
    doc.addSourceDescriptor(name="A b", designLocation={"Weight": 1})
    doc.addSourceDescriptor(name="A?b", designLocation={"Weight": 9})
    font = Font()
    font.layers.newLayer("A b")
    font.layers.newLayer("A?b")
    with pytest.raises(ValueError, match="collide"):
        write_designspace(font, doc, tmp_path / "Demo.designspace")


def test_export_when_native_snapshot_then_axes_come_from_the_package(tmp_path):
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
        instances=[SimpleNamespace(name="Medium", location={"wt": 500})],
    )
    backend = UFOBackend(two_master_font())
    backend._package = lambda: package
    path, losses = export_designspace(backend, tmp_path / "Demo.designspace")
    reopened = DesignSpaceDocument.fromfile(path)
    assert [s.name for s in reopened.sources] == ["Light", "Bold"]
    assert reopened.sources[1].designLocation == {"Weight": 900}
    assert reopened.instances[0].designLocation == {"Weight": 500}
    assert set(LOSSES) <= set(losses)
    assert not backend.closed, "the borrowed backend stays open"
