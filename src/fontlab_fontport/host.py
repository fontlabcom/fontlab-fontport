# this_file: src/fontlab_fontport/host.py
"""A bounded FontParts backend for registered FontLab documents.

Imports of fontlab/fontgate/PythonQt occur only at native boundaries. Handles
contain package ids, never retained native glyph/layer pointers. Validation is
staged before mutation; unexpected native assignment failures are not atomic.
Glyph notification calls are not a promise of Edit > Undo support; info updates
have a separately verified package/master checkpoint protocol.
"""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping
from typing import Any

from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import RecordingPointPen
from fontTools.pens.transformPen import TransformPointPen
from ufoLib2.objects import Glyph

from .errors import StaleObjectError, UnsupportedCapability
from .info import (
    INFO_FIELDS,
    INTEGER_FIELDS,
    READ_ONLY_FIELDS,
    STEM_SNAP_FIELDS,
    normalize_info,
    stage_info,
)
from .paths import absolute_path
from .pens import _draw_contour
from .transfer import _check_source, _lib_copy, write_glyph


def _edit_guards() -> Any:
    """FontLab write guards from App; native writes need ``fontlab-fontport[fontlab]``."""
    try:
        import fontlabapp.core.edit_guards as guards
    except ModuleNotFoundError as error:
        if error.name != "fontlabapp" and not (error.name or "").startswith("fontlabapp."):
            raise
        raise UnsupportedCapability(
            "native.write.guards",
            "Native FontLab writes need fontlab-fontlabapp: install fontlab-fontport[fontlab]",
        ) from error
    return guards


def _check_lib(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _check_lib(item)
    elif isinstance(value, list):
        for item in value:
            _check_lib(item)
    elif type(value) not in (str, bool, int, float):
        raise UnsupportedCapability(
            "lib.nativeJson",
            "Native live lib supports JSON scalar, list and dictionary data",
        )
    elif isinstance(value, (int, float)) and (
        abs(value) > 2**53 or not math.isfinite(value)
    ):
        raise ValueError(
            "Native live lib numbers must be finite and within the exact JSON integer range"
        )


def _stage_source(source: Any) -> Glyph:
    source = _check_source(source)
    for anchor in source.anchors:
        if any(float(v) != int(v) for v in (anchor.x, anchor.y)):
            raise UnsupportedCapability(
                "glyph.anchor.precision",
                "Native FontLab anchors lose fractional coordinates",
            )
    lib = _lib_copy(source.lib)
    _check_lib(lib)
    result = Glyph(name=source.name, lib=lib)
    for field in ("width", "height", "unicodes", "note"):
        setattr(result, field, copy.deepcopy(getattr(source, field)))
    result.anchors = [dict(a) for a in source.anchors]
    source.drawPoints(result.getPointPen())
    result.contours = [contour for contour in result.contours if len(contour)]
    return result


def _shape_problem(shape: Any) -> str | None:
    """Name why a native outline shape cannot be rewritten in place, if it cannot."""
    if not shape.transform.isIdentity():
        return "transformed"
    if shape.isComposite:
        return "composite"
    if not shape.image.isNull():
        return "image"
    if shape.shapeData.referenceCount > 1:
        return "shared"
    return None


def _carriers(shapes: list) -> list:
    """Outline shapes of ``shapes`` that currently hold contours."""
    return [s for s in shapes if not s.isComponent and len(s.contours)]


def _components(glyph: Any) -> list:
    return [(c.baseGlyph, tuple(c.transformation)) for c in glyph.components]


def _check_contour_carrier(outlines: list, source: Any, current: Any) -> None:
    """Issue 241: accept a several-shape layer only for the narrow proven case."""

    def refuse(reason: str) -> None:
        raise UnsupportedCapability(
            "glyph.geometry",
            f"{reason} on a native layer with several shapes is unsupported",
        )

    if current is None or _components(source) != _components(current):
        refuse("Changing components together with contours")
    if any(s.isComposite for s in outlines):
        refuse("Editing composite native shapes")
    carriers = _carriers(outlines)
    if len(carriers) != 1:
        refuse(
            "Contours spread over several native shapes"
            if carriers
            else "Adding contours where no native shape holds contours"
        )
    problem = _shape_problem(carriers[0])
    if problem:
        refuse(f"Editing a {problem} native contour shape")


def _geometry(source: Any) -> list:
    pen = RecordingPointPen()
    source.drawPoints(pen)
    return pen.value


class NativeFontBackend:
    """Attach to a registered document by id.

    Borrowed handles close only their binding. Set owns_document=True only for
    an explicitly owned document: close then discards its unsaved changes.
    Glyph metadata is global; widths/outlines/anchors belong to the named layer.
    New glyphs are created in all master layers. Whole glyph deletion is refused;
    remove_glyph removes only a non-master layer without deleting other layers.
    """

    requires_complete_contours = True
    glyph_global_fields = ("unicodes", "note", "lib")

    def __init__(self, font_id: int, *, owns_document: bool = False) -> None:
        if type(font_id) is not int or font_id <= 0:
            raise ValueError("font_id must be a positive registered package id")
        self.font_id = font_id
        self.owns_document = owns_document
        self._closed = False
        self._saved_path = None
        self._package()

    def _package(self) -> Any:
        if self._closed:
            raise StaleObjectError("Font binding is closed")
        import fontlab

        package = fontlab.flWorkspace.instance().findPackageId(self.font_id)
        if package is None or package.isNull:
            raise StaleObjectError("Font document has been closed")
        return package

    def check_open(self) -> None:
        self._package()

    def check_glyph(self, name: str, layer: str) -> None:
        try:
            self._target(name, layer)
        except KeyError as error:
            raise StaleObjectError(
                f"Stale glyph/layer binding: {name!r}/{layer!r}"
            ) from error

    def has_glyph(self, name: str, layer: str) -> bool:
        """Return whether ``name`` exists on ``layer``, without listing the font."""
        try:
            self._target(name, layer)
        except KeyError:
            return False
        return True

    def has_layer(self, name: str) -> bool:
        package = self._package()
        return name in package.masters or name in self.layer_names()

    def capabilities(self) -> dict:
        """Static capability metadata; valid after the document has closed."""
        from .capabilities import NATIVE_CAPABILITIES

        return copy.deepcopy(NATIVE_CAPABILITIES)

    def _target(self, name: str, layer: str) -> tuple[Any, Any, Any]:
        package = self._package()
        glyph = package.findName(name)
        if glyph is None or glyph.isNull:
            raise KeyError(name)
        target = glyph.findLayer(layer)
        if target is None or target.isNull:
            raise KeyError((name, layer))
        return package, glyph, target

    def layer_names(self) -> tuple[str, ...]:
        package = self._package()
        names = list(package.masters)
        for native in package.fgPackage:
            glyph = package.findName(native.name)
            for layer in glyph.layers:
                if layer.name not in names:
                    names.append(layer.name)
        return tuple(names)

    def default_layer(self) -> str:
        return self._package().defaultMaster

    def glyph_names(self, layer: str) -> tuple[str, ...]:
        return tuple(native.name for native, _ in self._layer_rows(layer))

    def glyph_summaries(self, layer: str) -> tuple[tuple[str, tuple[int, ...], float], ...]:
        """``(name, unicodes, advance width)`` of every glyph on ``layer``, in one pass."""
        return tuple(
            (native.name, tuple(native.unicodes), target.advanceWidth)
            for native, target in self._layer_rows(layer)
        )

    def _layer_rows(self, layer: str):
        package = self._package()
        # A master needs no font-wide layer scan; only other layers do.
        if layer not in package.masters and layer not in self.layer_names():
            raise KeyError(layer)
        for native in package.fgPackage:
            target = package.findName(native.name).findLayer(layer)
            if target is not None and not target.isNull:
                yield native, target

    def read_glyph(self, name: str, layer: str) -> Glyph:
        package, glyph, target = self._target(name, layer)
        import fontgate

        result = Glyph(
            name=name,
            lib=_lib_copy(glyph.lib),
            note=self._glyph_note(glyph),
            width=target.advanceWidth,
            height=target.advanceHeight,
            unicodes=list(self._fontgate_glyph(package, glyph).unicodes),
        )
        tx = target.transform
        transform = Transform(tx.m11(), tx.m12(), tx.m21(), tx.m22(), tx.dx(), tx.dy())
        pen = TransformPointPen(result.getPointPen(), transform)
        for shape in target.shapes:
            if shape.isComponent:
                t = shape.transform
                pen.addComponent(
                    shape.shapeData.componentGlyph,
                    (t.m11(), t.m12(), t.m21(), t.m22(), t.dx(), t.dy()),
                )
                continue
            native = fontgate.fgShape()
            shape.convertToFgShape(native)
            shape_pen = TransformPointPen(pen, native.matrix.asTuple())
            for contour in native.contours:
                _draw_contour(contour, shape_pen)
        for pin in target.anchors:
            point = pin.point
            result.appendAnchor({"name": pin.name, "x": point.x(), "y": point.y()})
        return result

    def _fontgate_glyph(self, package: Any, glyph: Any) -> Any:
        """Resolve the registered owner's record without exporting flGlyph data."""
        if package.fgId != self.font_id or glyph.package.id != package.id:
            raise StaleObjectError("Glyph no longer belongs to the registered font")
        # flGlyph.fgGlyph rebuilds native data and can drop a fresh lib.note.
        # This package came from _package(); never use fgPackage on an orphan.
        font = package.fgPackage
        if font is None or font.id != package.fgId:
            raise StaleObjectError("Registered FontGate font identity changed")
        # keys() retains duplicate names without exporting glyph data.
        if font.keys().count(glyph.name) != 1:
            raise StaleObjectError(
                "Registered FontGate glyph name is missing or ambiguous"
            )
        record = font[glyph.name]
        if record is None or record.name != glyph.name or record.id != glyph.fgGlyphId:
            raise StaleObjectError("Registered FontGate glyph identity changed")
        return record

    def _glyph_note(self, glyph: Any) -> str:
        # The native getter prefers the active layer note. Read global metadata
        # from the native serializer only in that ambiguous case; never apply
        # its incomplete glyph JSON back to the document.
        active = glyph.activeLayer
        if active is None or not active.note:
            return glyph.note
        import fontpr

        return fontpr.call(
            "get_glyph", font_id=self.font_id, glyph_name=glyph.name
        ).get("note", "")

    def write_glyph(self, name: str, layer: str, source: Any) -> None:
        self.write_glyph_named(name, layer, source)

    def write_glyph_named(
        self,
        name: str,
        layer: str,
        source: Any,
        *,
        undo_name: str = "FontParts glyph edit",
    ) -> None:
        from .fontdata import _undo_name

        _undo_name(undo_name)
        self._safe_glyph_name(name)
        source = _stage_source(source)
        for component in source.components:
            self._safe_glyph_name(component.baseGlyph)
        current = self.read_glyph(name, layer)
        package, glyph, target = self._target(name, layer)
        geometry_changed = _geometry(source) != _geometry(current)
        import fontgate
        import fontlab
        from PythonQt import QtCore

        staged = fontgate.fgGlyph()
        write_glyph(source, staged)
        try:
            shapes = self._stage_shapes(
                package, target, staged, source, geometry_changed, current
            )
        except UnsupportedCapability:
            raise
        except NotImplementedError as error:
            raise UnsupportedCapability("glyph.geometry", str(error)) from error
        anchors = []
        for a in source.anchors:
            pin = fontlab.flPinPoint(QtCore.QPointF(a.x, a.y))
            pin.name = a.name
            anchors.append(pin)
        anchors_changed = list(source.anchors) != list(current.anchors)
        fields = ("width", "height", "unicodes", "lib", "note")
        if (
            not geometry_changed
            and not anchors_changed
            and all(
                getattr(source, field) == getattr(current, field) for field in fields
            )
        ):
            return
        edit_guards = _edit_guards()

        edit_guards.require_history_scope((glyph,), native=fontlab)
        package.checkInitHistoryState(0)
        history = [target, glyph]
        fontlab.flItems.notifyChangesApplied(undo_name, history)
        try:
            if geometry_changed:
                self._own_shapes(target)
                self._apply_shapes(target, shapes)
            if anchors_changed:
                for pin in list(target.anchors):
                    target.removeAnchor(pin)
                for pin in anchors:
                    target.addAnchor(pin)
            if source.width != current.width:
                target.advanceWidth = source.width
            if source.height != current.height:
                target.advanceHeight = source.height
            if source.unicodes != current.unicodes:
                self._fontgate_glyph(package, glyph).unicodes = list(source.unicodes)
            if source.lib != current.lib:
                # flGlyph's QVariant map, not the defective fgLib Python dumper.
                glyph.lib = dict(source.lib)
            if (source.note or "") != (current.note or ""):
                active = glyph.activeLayer
                saved_note = active.note if active is not None else None
                glyph.note = source.note or ""
                if active is not None:
                    active.note = saved_note
        finally:
            fontlab.flItems.notifyChangesApplied(undo_name, history)

    @staticmethod
    def _stage_shapes(
        package: Any,
        target: Any,
        staged: Any,
        source: Glyph,
        changed: bool,
        current: Glyph | None = None,
    ) -> list:
        """Stage replacement shapes, refusing every layer shape we cannot prove.

        A layer with several outline shapes is accepted only for a contours-only
        edit (``current`` has the same components) whose contours live in exactly
        one untransformed, unshared, non-composite shape; only that shape changes.
        """
        if not changed:
            return []
        import fontlab
        from PythonQt import QtGui

        if target.hasHints or target.hasTTData or target.hasTTH:
            raise UnsupportedCapability(
                "glyph.geometry",
                "Outline edits on hinted native layers are unsupported",
            )
        existing = list(target.shapes)
        components = [s for s in existing if s.isComponent]
        if components and [s.shapeData.componentGlyph for s in components] != [
            c.baseGlyph for c in source.components
        ]:
            raise UnsupportedCapability(
                "glyph.geometry",
                "Replacing/removing existing native components is unsupported",
            )
        outlines = [s for s in existing if not s.isComponent]
        if not target.transform.isIdentity():
            raise UnsupportedCapability(
                "glyph.geometry",
                "Outline edits on transformed native layers are unsupported",
            )
        several = len(outlines) > 1
        if several:
            _check_contour_carrier(outlines, source, current)
        for shape in outlines:
            problem = _shape_problem(shape)
            if problem and not several:
                raise UnsupportedCapability(
                    "glyph.geometry", f"Editing a {problem} native shape is unsupported"
                )
        result = []
        if staged.layer is not None:
            for native_shape in staged.layer.shapes:
                shape = fontlab.flShape()
                shape.assign(native_shape)
                result.append(shape)
        if several:
            return result  # contours only: every component shape stays untouched
        for c in source.components:
            base = package.findName(c.baseGlyph)
            if base is None or base.isNull or base.findLayer(target.name) is None:
                raise UnsupportedCapability(
                    "components.unresolvedBase",
                    f"Component base missing in layer: {c.baseGlyph}",
                )
            if base.findLayer(target.name).isNull:
                raise UnsupportedCapability(
                    "components.unresolvedBase",
                    f"Component base missing in layer: {c.baseGlyph}",
                )
            pending, seen = [c.baseGlyph], set()
            while pending:
                component_name = pending.pop()
                if component_name == target.glyph.name:
                    raise UnsupportedCapability(
                        "components.unresolvedBase", "Cyclic components are unsupported"
                    )
                if component_name in seen:
                    continue
                seen.add(component_name)
                component_glyph = package.findName(component_name)
                if component_glyph is None or component_glyph.isNull:
                    raise UnsupportedCapability(
                        "components.unresolvedBase",
                        f"Missing component base: {component_name}",
                    )
                component_layer = component_glyph.findLayer(target.name)
                if component_layer is not None:
                    pending.extend(
                        s.shapeData.componentGlyph
                        for s in component_layer.shapes
                        if s.isComponent
                    )
            shape = fontlab.flShape(c.baseGlyph, target.name)
            shape.transform = QtGui.QTransform(*c.transformation)
            result.append(shape)
        if outlines and result:
            result[0].assignStyle(outlines[0])
        return result

    @staticmethod
    def _own_shapes(target: Any) -> None:
        """Copy-on-write after the pre-change checkpoint protects Undo references.

        Matches Glyport's native-tested _own_shape protocol. Never mutate a
        shape still referenced by the layer's saved history state.
        """
        shapes = list(target.shapes)
        several = len(shapes) > 1 and sum(not s.isComponent for s in shapes) > 1
        owned = _carriers(shapes) if several else shapes
        for index, shape in enumerate(shapes):
            if not any(shape is o for o in owned):
                continue  # Issue 241: other shapes of a several-shape layer stay
            clone = shape.clone()
            target.removeShape(shape)
            target.insertShape(index, clone)

    @staticmethod
    def _apply_shapes(target: Any, shapes: list) -> None:
        # Retain the original outline shape object/style; layer hints and guides
        # remain untouched. Component shapes are explicitly owned geometry.
        old = [s for s in target.shapes if not s.isComponent]
        several = len(old) > 1
        if several:
            old = _carriers(old)  # staging proved exactly one contour carrier
        plain = [s for s in shapes if not s.isComponent]
        if old:
            old[0].clearContours()
            old[0].shapeData.changed()
            if plain:
                old[0].addContours(list(plain[0].contours), False)
        elif plain:
            target.addShape(plain[0])
        if several:
            return
        components = [s for s in target.shapes if s.isComponent]
        incoming = [s for s in shapes if s.isComponent]
        if components:
            for old_shape, new_shape in zip(components, incoming, strict=True):
                old_shape.transform = new_shape.transform
                old_shape.changed()
        else:
            for shape in incoming:
                target.addShape(shape)

    def new_glyph(self, name: str, layer: str) -> None:
        self._safe_glyph_name(name)
        package = self._package()
        if not isinstance(name, str) or not name or "\x00" in name:
            raise ValueError("Glyph name must be nonempty text")
        if layer not in self.layer_names():
            raise KeyError(layer)
        existing = package.findName(name)
        if existing is not None and not existing.isNull:
            present = existing.findLayer(layer)
            if present is not None and not present.isNull:
                raise ValueError(f"Glyph already exists: {name}")
            import fontlab
            edit_guards = _edit_guards()

            edit_guards.require_history_scope((existing,), native=fontlab)
            existing.addLayer(fontlab.flLayer(layer))
            fontlab.flItems.notifyChangesApplied("FontParts new layer", [existing])
            return
        import fontlab
        edit_guards = _edit_guards()
        import fontpr

        edit_guards.require_history_scope((), creates=True, native=fontlab)
        fontpr.call(
            "set_glyph",
            font_id=self.font_id,
            glyph_name=name,
            create=True,
            glyph_data={
                "name": name,
                "layers": [
                    {"name": n, "advanceWidth": 0}
                    for n in dict.fromkeys((*package.masters, layer))
                ],
            },
        )
        self._target(name, layer)

    @staticmethod
    def _safe_glyph_name(name: str) -> None:
        if not isinstance(name, str) or not name or "\x00" in name:
            raise ValueError("Glyph name must be nonempty text")
        if not name.isascii():
            raise UnsupportedCapability(
                "glyph.name.unicodeVfj",
                "Non-ASCII glyph names can become mojibake on VFJ save (C4 kerning-source2); no write/history changed",
            )

    def rename_glyph(self, old: str, new: str, layer: str) -> None:
        self.check_open()
        self._safe_glyph_name(new)
        raise UnsupportedCapability(
            "glyph.rename",
            "Cross-layer component/kerning rename and VFJ preservation have no verified atomic route; no write/history changed",
        )

    def new_layer(self, name: str, color=None) -> None:
        self.check_open()
        raise UnsupportedCapability(
            "layer.create",
            "Native master/layer topology is not a UFO layer-set insertion; no write/history changed",
        )

    def remove_layer(self, name: str) -> None:
        self.check_open()
        raise UnsupportedCapability(
            "layer.delete",
            "Deleting a native master may change axes and other glyphs; no write/history changed",
        )

    def rename_layer(self, old: str, new: str) -> None:
        self.check_open()
        raise UnsupportedCapability(
            "layer.rename",
            "Native master rename requires package-wide topology changes; no write/history changed",
        )

    def remove_glyph(self, name: str, layer: str) -> None:
        package, glyph, target = self._target(name, layer)
        if layer in package.masters:
            raise UnsupportedCapability(
                "glyph.delete.master",
                "Master glyph deletion is unsupported; no layers were deleted",
            )
        import fontlab
        edit_guards = _edit_guards()

        edit_guards.require_history_scope((glyph,), native=fontlab)
        glyph.removeLayer(target)
        fontlab.flItems.notifyChangesApplied("FontParts remove layer glyph", [glyph])

    def get_info(self, attr: str) -> Any:
        package = self._package()
        if attr not in INFO_FIELDS and attr not in READ_ONLY_FIELDS:
            raise UnsupportedCapability(
                f"info.{attr}", f"Native info field unsupported: {attr}"
            )
        value = self._read_info(package, attr)
        if (
            (attr in READ_ONLY_FIELDS or attr in INTEGER_FIELDS)
            and isinstance(value, float)
            and value.is_integer()
        ):
            return int(value)  # UFO 3 stores these values as integers
        return value

    @staticmethod
    def _read_info(package, attr):
        if attr == "openTypeOS2Panose":
            text = package.panose
            return [int(value) for value in text.split()] if text else None
        if attr in ("openTypeOS2WeightClass", "openTypeOS2WidthClass"):
            field = (
                "weight_value" if attr == "openTypeOS2WeightClass" else "width_value"
            )
            return math.floor(float(getattr(package, field)) + 0.5)
        return normalize_info(attr, getattr(package.info, attr))

    @staticmethod
    def _write_info(package, attr, value):
        if attr == "openTypeOS2Panose":
            package.panose = " ".join(str(v) for v in value)
        elif attr == "openTypeOS2WeightClass":
            package.weight_value = value
        elif attr == "openTypeOS2WidthClass":
            package.width_value = value
        else:
            setattr(package.info, attr, value)

    def set_info(
        self, attr: str, value: Any, *, require_single_undo: bool = False
    ) -> None:
        self.set_info_many({attr: value}, require_single_undo=require_single_undo)

    def _refuse_unsafe_stem_snaps(self, package: Any, stems: list[str]) -> None:
        """Refuse stem-snap writes the native history cannot record (Issue 250 N3).

        A write to a non-active document gets no Undo row and leaves the
        document reporting clean; a write with unsaved history hides
        Undo/Redo and can go unrecorded. Both would silently lose data.
        """
        import fontlab

        current = fontlab.flWorkspace.instance().currentPackage
        if current is None or current.isNull or int(current.fgId) != int(package.fgId):
            reason = "the font is not the active document, so the native setter records no Undo row"
            advice = "Activate the font first"
        elif package.getProperty("__has_history_changes"):
            reason = "the native stem-snap setter disables Edit > Undo/Redo in a document with unsaved history and can leave the change unrecorded"
            advice = "Save the font, or write stem snaps before other edits"
        else:
            return
        raise UnsupportedCapability(
            "info.postscriptStemSnap.history",
            f"Refused {', '.join(stems)}: {reason}; no history or data changed. {advice}",
            checked_apis=(
                "flPackage.info.postscriptStemSnapH",
                "flPackage.info.postscriptStemSnapV",
                "flWorkspace.currentPackage",
                'flPackage.getProperty("__has_history_changes")',
            ),
        )

    def set_info_many(
        self,
        values: Mapping[str, Any],
        *,
        undo_name: str = "FontParts font info",
        require_single_undo: bool = False,
    ) -> None:
        """Apply validated fields as a named batch with native Undo checkpoints.

        package.info routes metrics to the current key master; its UPM setter
        changes only the stored UPM, without scaling glyphs or other metrics.
        A pre-edit package checkpoint makes the entire first Undo reliable.
        The host exposes this no-op checkpoint as an additional Undo row.
        Default editing preserves the v1.0.0 history contract (D18).
        Set require_single_undo=True to refuse the extra checkpoint.
        Changing postscriptStemSnapH/V is refused unless the font is the
        active document without unsaved history (Issue 250 N3).
        """
        package = self._package()
        staged = stage_info(values, undo_name)
        if "openTypeNameRecords" in staged and staged[
            "openTypeNameRecords"
        ] != self._read_info(package, "openTypeNameRecords"):
            raise UnsupportedCapability(
                "info.openTypeNameRecords.persistence",
                "The bound setter changes regenerated fg::Style names, not persisted localized storage; no history or data changed",
                checked_apis=(
                    "flPackage.info.openTypeNameRecords",
                    "flPackage::setLocalizedNames (not Python-bound)",
                ),
            )
        changed = {
            attr: value
            for attr, value in staged.items()
            if self._read_info(package, attr) != value
        }
        if not changed:
            return
        stems = sorted(STEM_SNAP_FIELDS.intersection(changed))
        if stems:
            self._refuse_unsafe_stem_snaps(package, stems)
        if require_single_undo:
            raise UnsupportedCapability(
                "info.exactSingleUndo",
                "The verified native protocol adds an extra no-op Undo checkpoint; strict batch refused before write/history changes",
            )
        package.checkInitHistoryState(0)
        import fontlab

        history = [package, package.mastersContainer()]
        # Existing package history may lack restorable package-global data,
        # even at nonzero indexes after a native glyph operation. The master
        # container alone restores only styleName, metrics and the font note.
        fontlab.flItems.notifyChangesApplied(undo_name, history)
        for attr, value in changed.items():
            self._write_info(package, attr, value)
        fontlab.flItems.notifyChangesApplied(undo_name, history)

    def path(self) -> str | None:
        package = self._package()
        return self._saved_path or package.path or None

    def get_groups(self) -> dict[str, tuple[str, ...]]:
        from .native_groups import read_groups

        return read_groups(self._package())[0]

    def set_groups(
        self,
        values: Mapping[str, Any],
        *,
        undo_name: str = "FontParts groups",
        require_persistence: bool = False,
    ) -> None:
        from .native_groups import write_groups

        write_groups(
            self._package(), values, undo_name, require_persistence=require_persistence
        )

    def save(
        self, path: str | None = None, *, require_persistence: bool = False
    ) -> None:
        package = self._package()
        destination = path or self.path()
        if destination is None:
            raise ValueError("A destination is required for an unsaved document")
        destination = absolute_path(destination)
        if destination.suffix.lower() not in (".vfj", ".vfc"):
            raise UnsupportedCapability(
                "font.save.format",
                "Native document save requires .vfj or .vfc; use whole-font UFO export",
            )
        if require_persistence:
            for glyph in package.fgPackage:
                self._safe_glyph_name(glyph.name)
        if require_persistence and destination.suffix.lower() == ".vfj":
            from .native_groups import check_persistence

            check_persistence(package)
        import fontpr

        fontpr.call(
            "save_font", font_id=self.font_id, path=str(destination), overwrite=True
        )
        if not destination.is_file():
            raise OSError(f"FontLab did not create {destination}")
        self._saved_path = str(destination)

    def get_kerning(self) -> dict[tuple[str, str], int | float]:
        from .native_kerning import read_kerning, target_master

        package = self._package()
        return read_kerning(package, target_master(package))

    def get_master_kerning(self, name: str):
        """Kerning of master ``name`` via flPackage.kerning(name); None if not a master."""
        from .native_kerning import read_kerning

        package = self._package()
        return read_kerning(package, name) if name in package.masters else None

    def set_kerning(
        self,
        values: Mapping[tuple[str, str], int | float],
        *,
        undo_name: str = "FontParts kerning",
    ) -> None:
        from .native_kerning import write_kerning

        write_kerning(self._package(), values, undo_name)

    def close(self) -> None:
        self._package()
        if self.owns_document:
            import fontpr

            fontpr.call("close_font", font_id=self.font_id, save=False)
        self._closed = True

    def get_feature_blocks(self) -> dict:
        from .native_features import read_blocks

        self._package()
        return read_blocks(self.font_id)

    def set_feature_blocks(
        self, values: Mapping, *, undo_name: str = "FontParts features"
    ) -> None:
        from .native_features import write_blocks

        write_blocks(self._package(), self.font_id, values, undo_name)

    def get_features(self) -> str:
        from .native_features import text_from_blocks

        return text_from_blocks(self.get_feature_blocks())

    def set_features(
        self, text: str | None, *, undo_name: str = "FontParts features"
    ) -> None:
        from .fontdata import _undo_name
        from .info import _text

        self._package()
        _undo_name(undo_name)
        if text is None:
            self.set_feature_blocks({"prefix": "", "features": []}, undo_name=undo_name)
            return
        _text(text, "features")
        if text == self.get_features():
            return
        raise UnsupportedCapability(
            "font.features.text.split",
            "Arbitrary whole-text splitting is not Python-bound. Use font.features.set_blocks "
            "or backend.set_feature_blocks with {prefix, features: [(tag, code), ...]}; "
            "no data/history changed.",
            checked_apis=("LayoutFea.setFeaText/loadFeaTextInfo (C++ only)",),
        )

    def get_lib(self) -> dict[str, Any]:
        from .fontdata import _arrays

        return _arrays(
            {
                k: v
                for k, v in dict(self._package().packageLib).items()
                if k != "com.fontlab.kerningClassesInMainMaster"
            }
        )

    def set_lib(
        self, values: Mapping[str, Any], *, undo_name: str = "FontParts lib"
    ) -> None:
        """Preserve untouched entries and use info's package/master checkpoints.

        First native lib Undo/Redo remains an explicit acceptance gate.
        """
        from .fontdata import _undo_name, changed_lib, same_lib

        package = self._package()
        _undo_name(undo_name)
        internal = "com.fontlab.kerningClassesInMainMaster"
        if internal in values:
            raise UnsupportedCapability("lib.reservedKey", f"FontLab owns {internal}")
        raw = dict(package.packageLib)
        current = self.get_lib()
        staged = changed_lib(current, values, value_validator=_check_lib)
        if same_lib(current, staged):
            return
        package.checkInitHistoryState(0)
        import fontlab

        history = [package, package.mastersContainer()]
        fontlab.flItems.notifyChangesApplied(undo_name, history)
        package.packageLib = {
            **{k: v for k, v in raw.items() if k == internal},
            **staged,
        }
        fontlab.flItems.notifyChangesApplied(undo_name, history)
