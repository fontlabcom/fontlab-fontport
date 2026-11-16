# this_file: src/fontlab_fontport/transfer.py
"""Detached glyph interchange; this module does not provide live font editing.

Writes replace selected-layer outlines and anchors plus glyph components and
metadata. The supplied native glyph keeps its name, other layers and unknown
state. Multi-shape and transformed targets are refused in this first stage.
Validation and native construction are staged before destination mutation;
native failures during final assignment are not a transactional undo facility.
"""

from __future__ import annotations

import copy
import math
import plistlib
from typing import Any
from xml.etree import ElementTree

from fontParts.base.glyph import BaseGlyph
from fontParts.fontshell import RGlyph
from ufoLib2.objects import Anchor, Glyph

from .errors import UnsupportedCapability
from .pens import FontGatePointPen, draw_points

_IDENTITY = (1, 0, 0, 1, 0, 0)
_FIELDS = ("width", "height", "unicodes", "note")


def _lib_copy(lib: Any) -> dict:
    # fgLib has no subscription protocol; get() parses serialized values.
    keys = lib.keys()
    data = copy.deepcopy({key: lib.get(key) for key in keys})
    return plistlib.loads(plistlib.dumps(data))


def _encoded_lib(data: dict) -> dict[str, str]:
    """Use the standard plist serializer instead of FontGate's legacy dumper.

    fgLib.update drops nested Python-3 dictionary keys and doesn't escape XML
    text. The typed fgGlyph.dict.lib mapping accepts serialized values by key.
    """
    return {
        key: ElementTree.tostring(
            ElementTree.fromstring(plistlib.dumps(value))[0], encoding="unicode"
        )
        for key, value in data.items()
    }


def _native_lib(glyph: Any) -> dict:
    """Decode raw fragments with plistlib, preserving arrays/data/date types."""
    result = {}
    for key, fragment in glyph.lib.items().items():
        if key == "note":
            result[key] = glyph.note
        else:
            result[key] = plistlib.loads(
                ("<plist version='1.0'>" + fragment + "</plist>").encode("utf-8")
            )
    return result


def to_ufo_glyph(native_glyph: Any) -> Glyph:
    """Copy selected outlines/anchors and glyph metadata to a ufoLib2 glyph.

    This interchange slice excludes native guides, hints and images. It never
    changes the native object or creates a live host proxy.
    """
    result = Glyph(name=native_glyph.name, lib=_native_lib(native_glyph))
    for field in _FIELDS:
        setattr(result, field, copy.deepcopy(getattr(native_glyph, field)))
    draw_points(native_glyph, result.getPointPen())
    layer = native_glyph.layer
    if layer is not None:
        for anchor in layer.anchors:
            position = anchor.position
            result.anchors.append(Anchor(position.x, position.y, name=anchor.name))
    return result


def to_fontparts(native_glyph: Any) -> RGlyph:
    """Return a detached upstream fontshell RGlyph with no parent font.

    Changes to the returned object do not write back to FontLab.
    """
    source = to_ufo_glyph(native_glyph)
    result = RGlyph()
    result.name = source.name
    for field in _FIELDS:
        setattr(result, field, copy.deepcopy(getattr(source, field)))
    result.lib.update(_lib_copy(source.lib))
    source.drawPoints(result.getPointPen())
    for anchor in source.anchors:
        result.appendAnchor(anchor.name, (anchor.x, anchor.y))
    return result


def _check_source(source: Any) -> Any:
    if isinstance(source, BaseGlyph):
        source = source.naked()
    if source.guidelines:
        raise UnsupportedCapability(
            "glyph.guidelines", "Glyph guidelines are not supported"
        )
    if source.image is not None and source.image.fileName is not None:
        raise UnsupportedCapability("glyph.image", "Glyph image is not supported")
    for anchor in source.anchors:
        if anchor.identifier is not None:
            raise UnsupportedCapability(
                "identifiers", "Native anchor identifiers cannot be persisted"
            )
        if anchor.color is not None:
            raise UnsupportedCapability(
                "glyph.anchor.metadata", "Anchor identifier and color are not supported"
            )
        if not all(math.isfinite(v) for v in (anchor.x, anchor.y)):
            raise ValueError("Anchor coordinates must be finite")
        if not isinstance(anchor.name, str):
            raise UnsupportedCapability(
                "glyph.anchor.name", "Unnamed anchors are not supported"
            )
    for field in ("width", "height"):
        if not math.isfinite(getattr(source, field)):
            raise ValueError(f"{field} must be finite")
    if source.note is not None and not isinstance(source.note, str):
        raise TypeError("note must be a string or None")
    if any(
        type(value) is not int
        or (not 0 <= value <= 0x10FFFF or 0xD800 <= value <= 0xDFFF)
        for value in source.unicodes
    ):
        raise ValueError("unicodes must contain Unicode scalar integers")
    return source


def _check_target(glyph: Any) -> None:
    layer = glyph.layer
    if layer is None:
        return
    shapes = list(layer.shapes)
    if len(shapes) > 1:
        raise UnsupportedCapability(
            "glyph.shapes.multiple",
            "Writing a target with multiple shapes is not supported",
        )
    if tuple(layer.matrix.asTuple()) != _IDENTITY or any(
        tuple(shape.matrix.asTuple()) != _IDENTITY for shape in shapes
    ):
        raise UnsupportedCapability(
            "glyph.shapes.transform",
            "Writing a transformed target layer/shape is not supported",
        )


def _set_metadata(target: Any, source: Any, lib: dict) -> None:
    # Whole-dictionary assignment through dict.lib has a native value/key bug.
    # Individual typed-map assignments bypass that and the old fgLib dumper.
    encoded = _encoded_lib(lib)
    target.lib.clear()
    raw = target.dict.lib
    for key, value in encoded.items():
        raw[key] = value
    for field in _FIELDS:
        value = copy.deepcopy(getattr(source, field))
        # Native note is a string; absent UFO notes map to an empty string.
        setattr(target, field, "" if field == "note" and value is None else value)


def write_glyph(source: Any, native_glyph: Any) -> None:
    """Replace an explicit native target from FontParts, defcon or ufoLib2.

    The destination name is retained even when the source name differs.
    Identifiers, anchor colors, unnamed anchors, guidelines and images are
    refused before mutation. Only the selected layer's contours/anchors are
    replaced; hints, guides, shape style and other layers are left in place.
    """
    source = _check_source(source)
    _check_target(native_glyph)
    lib = _lib_copy(source.lib)
    import fontgate

    staged = fontgate.fgGlyph()
    _set_metadata(staged, source, lib)
    source.drawPoints(FontGatePointPen(staged, native=fontgate))
    anchors = [fontgate.fgAnchor(a.name, a.x, a.y) for a in source.anchors]
    # All incoming geometry, metadata and native anchors now exist independently.
    layer = native_glyph.layer
    if layer is not None:
        for shape in layer.shapes:
            shape.contours.clean()
        layer.anchors.clean()
    else:
        native_glyph.anchors.clean()
    native_glyph.components.clean()
    draw_points(staged, FontGatePointPen(native_glyph, native=fontgate))
    target_anchors = (
        native_glyph.layer.anchors
        if native_glyph.layer is not None
        else native_glyph.anchors
    )
    for anchor in anchors:
        target_anchors.append(anchor)
    _set_metadata(native_glyph, staged, lib)
