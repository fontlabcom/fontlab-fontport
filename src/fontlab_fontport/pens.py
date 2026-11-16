# this_file: src/fontlab_fontport/pens.py
"""Glyph-level adapter over `fontlab_pens.fontgate`.

Fontport's native model is an fgGlyph whose outline lives on `glyph.layer`,
with glyph-level components. Pens target layers and elements only, so this
module resolves the glyph itself: contours are validated, then written by
`fontlab_pens.fontgate.FontGatePointPen` into the layer's first element (point
names and smooth flags kept); components stay on `glyph.components`. Empty
native contours are never passed to fgContour.drawPoints, whose implementation
dereferences the first node without checking its existence.

The target kind is stated to pens (`kind=`), not detected from the native type
name, so the same code serves FontGate objects and the duck-typed offline doubles.
Only public `fontlab_pens` names are used.
"""

from __future__ import annotations

from typing import Any

from fontlab_pens import (
    FONTGATE_NODE_TYPES,
    IncompleteContour,
    PenError,
    StagedPoint,
    StagingPointPen,
    Transform,
    invert_transform,
    staged_node_kinds,
)
from fontlab_pens.fontgate import FontGatePointPen as _TargetPointPen
from fontlab_pens.fontgate import draw_contour_points as _draw_contour
from fontlab_pens.point import AbstractPointPen

from .errors import UnsupportedCapability

__all__ = [
    "FontGatePointPen",
    "IncompleteContour",
    "draw_points",
    "edit_geometry_ready",
]


def _no_identifier(identifier: str | None) -> None:
    if identifier is not None:
        raise UnsupportedCapability(
            "identifiers", "FontGate does not store UFO object identifiers"
        )


def _matrix(native_object: Any) -> Transform:
    return Transform(*native_object.matrix.asTuple())


class FontGatePointPen(StagingPointPen):
    """Append a complete contour to a glyph only after its geometry validates.

    A contour goes to `glyph.layer.shapes[0]`, mapped through the inverse of
    layer x element matrices; a layer without elements gets one new element.
    A glyph without a layer keeps the native `createContour()` route with
    identity mapping, which lets FontGate allocate the layer.
    """

    def __init__(self, glyph: Any, *, native: Any = None) -> None:
        super().__init__()
        self.glyph = glyph
        self.native = native

    def _native(self) -> Any:
        if self.native is None:
            import fontgate

            self.native = fontgate
        return self.native

    def beginPath(self, identifier: str | None = None, **kwargs: Any) -> None:
        _no_identifier(identifier)
        super().beginPath(**kwargs)

    def addPoint(
        self,
        pt: tuple,
        segmentType: str | None = None,
        smooth: bool = False,
        name: str | None = None,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        _no_identifier(identifier)
        super().addPoint(pt, segmentType, smooth, name, **kwargs)

    def append_contour(self, points: list[StagedPoint]) -> None:
        layer = self.glyph.layer
        if layer is None:
            self._create_contour(points)
            return
        shapes = layer.shapes
        if len(shapes):
            # Pens maps an element through its own matrix; add the layer's here.
            to_layer = invert_transform(_matrix(layer))
            points = [(to_layer.transformPoint(p), *rest) for p, *rest in points]
            target = _TargetPointPen(shapes[0], native=self._native(), kind="element")
        else:
            target = _TargetPointPen(layer, native=self._native(), kind="layer")
        target.append_contour(points)

    def _create_contour(self, points: list[StagedPoint]) -> None:
        native = self._native()
        contour = self.glyph.createContour()
        contour.nodes = [
            native.fgNode(
                FONTGATE_NODE_TYPES[kind], native.fgPoint(*position), name or "", smooth
            )
            for (position, _, smooth, name), kind in zip(
                points, staged_node_kinds(points), strict=True
            )
        ]
        contour.open = points[0][1] == "move"

    def addComponent(
        self,
        baseGlyphName: str,
        transformation: tuple,
        identifier: str | None = None,
        **kwargs: Any,
    ) -> None:
        _no_identifier(identifier)
        matrix = self.check_component(transformation)
        self.glyph.components.append(baseGlyphName, matrix)


def draw_points(glyph: Any, pen: AbstractPointPen) -> None:
    """Read native points without invoking unsafe native empty-contour code."""
    layer = glyph.layer
    if layer is not None:
        base = _matrix(layer)
        for shape in layer.shapes:
            mapping = base.transform(_matrix(shape))
            for contour in shape.contours:
                _draw_contour(contour, pen, mapping)
    for component in glyph.components:
        component.drawPoints(pen)


class _GeometryProbe(FontGatePointPen):
    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        _no_identifier(
            identifier
        )  # Geometry validation must allocate no native components.

    def append_contour(self, points):
        pass  # Validation only, no native allocation.


def edit_geometry_ready(glyph: Any) -> bool:
    """Provisional point edits stay in Python until their pen geometry is valid.

    No geometry is guessed or repaired. Invalid input to a standalone pen still
    raises; a retained live contour can be built a point at a time and corrected.
    """
    try:
        glyph.drawPoints(_GeometryProbe(None))
    except (IncompleteContour, PenError):
        return False
    return True
