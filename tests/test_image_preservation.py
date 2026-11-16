# this_file: tests/test_image_preservation.py
"""Owned, real-library image metadata preservation across detached boundaries."""

import base64
import hashlib
from copy import deepcopy

import pytest
from ufoLib2 import Font
from ufoLib2.objects import Anchor, Guideline, Image

from fontlab_fontport.live import RFont
from fontlab_fontport.memory import UFOBackend

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg=="
)
TRANSFORM = (1.25, 0.2, -0.1, 0.9, 13.5, -17.75)
COLOR = "0.125,0.25,0.5,0.75"


def owned_font(with_image=True):
    font = Font()
    font.info.familyName = "Owned Image Preservation"
    font.info.styleName = "Regular"
    font.info.unitsPerEm = 1000
    font.info.ascender = 800
    font.info.descender = -200
    font.lib["owned"] = {"nested": [True, 1, "control"]}
    font.features.text = "feature liga { sub A B by A; } liga;"
    font.groups["public.kern1.owned"] = ["A"]
    font.kerning[("A", "B")] = -25
    font.images["owned.png"] = PNG
    font.data["owned/payload.bin"] = b"owned\0\xff"
    glyph = font.newGlyph("A")
    glyph.width, glyph.height = 600, 900
    glyph.unicodes = [65]
    glyph.note = "Owned non-target note"
    glyph.lib["owned"] = {"nested": [1, 2, 3]}
    if with_image:
        glyph.image = Image("owned.png", TRANSFORM, COLOR)
    glyph.anchors = [Anchor(100, 700, "top", "0,0,1,1", "owned-anchor")]
    glyph.guidelines = [
        Guideline(25, 0, 90, "owned-guide", identifier="owned-guideline")
    ]
    pen = glyph.getPointPen()
    pen.beginPath(identifier="owned-contour")
    for index, point in enumerate(((0, 0), (100, 0), (100, 100), (0, 100))):
        pen.addPoint(
            point,
            segmentType="line",
            name=f"p{index}",
            identifier=f"owned-point-{index}",
        )
    pen.endPath()
    pen.addComponent("B", (1, 0, 0, 1, 10, 20), identifier="owned-component")
    font.newGlyph("B").width = 420
    other = font.layers.newLayer("owned.background")
    other.color = "0.1,0.2,0.3,1"
    other.lib["owned-layer"] = ["unchanged"]
    other.newGlyph("untouched").width = 333
    return font


def file_hashes(path):
    return {
        str(item.relative_to(path)): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in path.rglob("*")
        if item.is_file()
    }


@pytest.mark.parametrize("route", ["backend_noop", "width", "point"])
@pytest.mark.parametrize("structure", ["package", "zip"])
@pytest.mark.parametrize("with_image", [True, False])
def test_image_metadata_when_editing_then_complete_saved_font_matches_control(
    tmp_path, route, structure, with_image
):
    initial = tmp_path / "input.ufo"
    owned_font(with_image).save(initial)
    initial_hashes = file_hashes(initial)
    backend = UFOBackend(Font.open(initial, lazy=False))
    expected = Font.open(initial, lazy=False)
    layer = backend.default_layer()
    if route == "backend_noop":
        backend.write_glyph("A", layer, backend.read_glyph("A", layer))
    else:
        checked = RFont(backend)["A"]
        assert dict(checked.naked().image) == dict(expected["A"].image)
        if route == "width":
            checked.width = 617
            expected["A"].width = 617
        else:
            checked[0].points[0].x = 9
            expected["A"].contours[0].points[0].x = 9
    assert backend.font == expected
    actual_path = tmp_path / ("actual.ufoz" if structure == "zip" else "actual.ufo")
    expected_path = tmp_path / (
        "expected.ufoz" if structure == "zip" else "expected.ufo"
    )
    backend.save_options(actual_path, fileStructure=structure)
    expected.save(expected_path, structure=structure)
    actual = Font.open(actual_path, lazy=False)
    control = Font.open(expected_path, lazy=False)
    assert actual == control
    assert dict(actual["A"].image) == dict(control["A"].image)
    assert actual.images["owned.png"] == control.images["owned.png"] == PNG
    assert actual.data["owned/payload.bin"] == b"owned\0\xff"
    assert file_hashes(initial) == initial_hashes


def test_image_when_copied_then_source_and_checked_objects_are_independent():
    backend = UFOBackend(owned_font())
    layer = backend.default_layer()
    source = backend.read_glyph("A", layer)
    backend.write_glyph("A", layer, source)
    checked = RFont(backend)["A"]
    expected_image = dict(source.image)
    source.image.transformation = (1, 0, 0, 1, 999, 999)
    source.lib["owned"]["nested"].append(999)
    assert dict(backend.font["A"].image) == expected_image
    assert dict(checked.naked().image) == expected_image
    assert backend.font["A"].lib["owned"]["nested"] == [1, 2, 3]
    backend.font["A"].image.color = "1,0,0,1"
    assert dict(checked.naked().image) == expected_image


def test_image_when_supported_transform_changes_then_real_notification_persists():
    backend = UFOBackend(owned_font())
    expected = deepcopy(backend.font)
    changed = (1.5, 0.1, -0.2, 0.8, 21.5, -31.25)
    checked = RFont(backend)["A"]
    checked.image.transformation = changed
    expected["A"].image.transformation = changed
    assert backend.font == expected
    assert backend.font.images["owned.png"] == PNG


def test_image_when_backend_write_fails_then_accepted_glyph_is_restored():
    class RejectingBackend(UFOBackend):
        def write_glyph(self, name, layer, source):
            raise OSError("owned write rejected")

    backend = RejectingBackend(owned_font())
    expected = deepcopy(backend.font)
    checked = RFont(backend)["A"]
    accepted_image = dict(expected["A"].image)
    with pytest.raises(OSError, match="owned write rejected"):
        checked.width = 617
    assert checked.width == 600
    assert dict(checked.naked().image) == accepted_image
    with pytest.raises(OSError, match="owned write rejected"):
        checked.image.transformation = (1, 0, 0, 1, 999, 999)
    assert dict(checked.naked().image) == accepted_image
    assert backend.font == expected


def test_image_when_backend_receives_real_fontparts_wrapper_then_preserves_fields():
    from fontParts.fontshell import RGlyph

    backend = UFOBackend(owned_font())
    source = RGlyph()
    source.naked().image = dict(backend.font["A"].image)
    source.width = 617
    backend.write_glyph("A", backend.default_layer(), source)
    assert dict(backend.font["A"].image) == {
        "fileName": "owned.png",
        "xScale": 1.25,
        "xyScale": 0.2,
        "yxScale": -0.1,
        "yScale": 0.9,
        "xOffset": 13.5,
        "yOffset": -17.75,
        "color": COLOR,
    }
    assert backend.font["A"].width == 617


def test_image_when_defcon_clears_fields_incrementally_then_default_is_persisted():
    backend = UFOBackend(owned_font())
    expected = deepcopy(backend.font)
    checked = RFont(backend)["A"]
    checked.clearImage()
    expected["A"].image = None
    assert backend.font == expected
    assert dict(checked.naked().image) == dict(expected["A"].image)
    assert backend.font.images["owned.png"] == PNG


@pytest.mark.parametrize("route", ["noop", "width", "point"])
@pytest.mark.parametrize("structure", ["package", "zip"])
def test_image_when_staged_edit_then_complete_saved_font_matches_control(
    tmp_path, route, structure
):
    initial = tmp_path / "input.ufo"
    owned_font().save(initial)
    initial_hashes = file_hashes(initial)
    backend = UFOBackend(Font.open(initial, lazy=False))
    expected = Font.open(initial, lazy=False)
    font = RFont(backend)
    with font.edit_glyph("A") as staged:
        assert dict(staged.naked().image) == dict(expected["A"].image)
        if route == "width":
            staged.width = 617
            expected["A"].width = 617
        elif route == "point":
            staged[0].points[0].x = 9
            expected["A"].contours[0].points[0].x = 9
    assert backend.font == expected
    actual_path = tmp_path / ("actual.ufoz" if structure == "zip" else "actual.ufo")
    expected_path = tmp_path / (
        "expected.ufoz" if structure == "zip" else "expected.ufo"
    )
    backend.save_options(actual_path, fileStructure=structure)
    expected.save(expected_path, structure=structure)
    actual = Font.open(actual_path, lazy=False)
    assert actual == Font.open(expected_path, lazy=False)
    assert dict(actual["A"].image) == dict(expected["A"].image)
    assert actual.images["owned.png"] == PNG
    assert actual.data["owned/payload.bin"] == b"owned\0\xff"
    assert file_hashes(initial) == initial_hashes


def test_image_when_staged_body_fails_then_original_font_is_unchanged():
    backend = UFOBackend(owned_font())
    expected = deepcopy(backend.font)
    with (
        pytest.raises(RuntimeError, match="owned staged body rejected"),
        RFont(backend).edit_glyph("A") as staged,
    ):
        assert dict(staged.naked().image) == dict(expected["A"].image)
        staged.image.transformation = (1, 0, 0, 1, 999, 999)
        raise RuntimeError("owned staged body rejected")
    assert backend.font == expected


def test_image_when_staged_backend_rejects_then_original_font_is_unchanged():
    class RejectingBackend(UFOBackend):
        def write_glyph(self, name, layer, source):
            raise OSError("owned staged write rejected")

    backend = RejectingBackend(owned_font())
    expected = deepcopy(backend.font)
    with (
        pytest.raises(OSError, match="owned staged write rejected"),
        RFont(backend).edit_glyph("A") as staged,
    ):
        assert dict(staged.naked().image) == dict(expected["A"].image)
        staged.width = 617
    assert backend.font == expected
