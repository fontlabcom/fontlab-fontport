# this_file: src/fontlab_fontport/interchange.py
"""Incremental whole-UFO interchange with explicit native preflight refusals.

Each iterator step handles one glyph or one metadata family. Exhaust preflight
before creating a destination. The source is borrowed; imported fonts are owned
by the context manager and are closed even when applying a step fails.
"""

from contextlib import contextmanager
from copy import deepcopy

from fontTools.ufoLib import validateFontInfoVersion3ValueForAttribute
from ufoLib2 import Font

from .errors import UnsupportedCapability
from .info import INFO_FIELDS, STEM_SNAP_FIELDS
from .native_feature_split import split_history_text
from .native_features import stage_blocks, text_from_blocks
from .paths import absolute_path

BLOCKS_KEY = "org.fontlab.fontport.featureBlocks"
NATIVE_LOSSES = (
    "Native hints, TT programs, masks, shape style/transforms and image data have no UFO equivalent in this adapter",
    "Native glyph/layer guidelines, colors and identifiers are not read by NativeFontBackend",
    "Native axes, instances, brace layers and per-master groups/kerning are not preserved as a variable-font model; named layers are exported",
    "Only INFO_FIELDS have native accessors; all other UFO info fields remain absent",
    "Legacy group flags and kerning-class key glyphs are absent from the UFO groups mapping",
    "Font-level lib must be plist-compatible; foreign JSON null is refused on serialization, never silently removed",
)


class ExportSession:
    def __init__(self, backend):
        self.backend = backend
        self.font = Font()
        default = backend.default_layer()
        if default != self.font.layers.defaultLayer.name:
            self.font.layers.renameLayer(self.font.layers.defaultLayer.name, default)
        self.losses = list(NATIVE_LOSSES) if hasattr(backend, "font_id") else []
        self.master_kerning: dict[str, dict] = {}
        self.complete = False

    def steps(self):
        """Read all layers/glyphs, then each metadata family independently."""
        for name in self.backend.layer_names():
            layer = (
                self.font.layers[name]
                if name in self.font.layers
                else self.font.layers.newLayer(name)
            )
            for glyph in self.backend.glyph_names(name):
                layer.insertGlyph(self.backend.read_glyph(glyph, name), overwrite=False)
                yield {"kind": "glyph", "layer": name, "name": glyph}
        for attr in sorted(INFO_FIELDS):
            try:
                value = self.backend.get_info(attr)
                if value is not None and not validateFontInfoVersion3ValueForAttribute(
                    attr, value
                ):
                    self.losses.append(
                        f"info.{attr}: native value {value!r} is invalid in UFO 3; exported absent"
                    )
                    value = None
                setattr(self.font.info, attr, value)
            except NotImplementedError as error:
                self.losses.append(f"info.{attr}: {error}")
            yield {"kind": "info", "name": attr}
        for attr in ("groups", "kerning", "lib"):
            value = deepcopy(getattr(self.backend, "get_" + attr)())
            if attr == "lib":
                from .fontdata import stage_lib

                try:
                    value = stage_lib(value)
                except (ValueError, TypeError) as error:
                    raise UnsupportedCapability(
                        "ufo.export.lib.plist", str(error)
                    ) from error
            setattr(self.font, attr, value)
            yield {"kind": attr}
        reader = getattr(self.backend, "get_master_kerning", None)
        for name in self.backend.layer_names() if reader else ():
            pairs = reader(name)
            if pairs is not None:
                self.master_kerning[name] = deepcopy(pairs)
                yield {"kind": "masterKerning", "name": name}
        if hasattr(self.backend, "font_id") and hasattr(
            self.backend, "get_feature_blocks"
        ):
            if BLOCKS_KEY in self.font.lib:
                raise ValueError(
                    f"Reserved interchange lib key already present: {BLOCKS_KEY}"
                )
            blocks = self.backend.get_feature_blocks()
            self.font.lib[BLOCKS_KEY] = blocks
            self.font.features.text = text_from_blocks(blocks)
        else:
            self.font.features.text = self.backend.get_features() or ""
        yield {"kind": "features"}
        self.complete = True

    def save(self, destination):
        if not self.complete:
            raise RuntimeError("Exhaust export steps before saving")
        target = absolute_path(destination)
        if target.suffix.lower() != ".ufo":
            raise ValueError("Whole-font destination requires .ufo")
        if target.exists():
            raise FileExistsError(target)
        self.font.save(target)
        return target


def preflight_import(source: Font, *, native=False):
    """Yield checked units; allocate no native objects and perform no writes."""
    if native and len(source.layers) != 1:
        raise UnsupportedCapability(
            "ufo.import.layers",
            "Native master/layer creation is unavailable; destination was not created",
        )
    for layer in source.layers:

        def check_cycle(name, ancestry=(), layer=layer):
            if name in ancestry:
                if native:
                    raise UnsupportedCapability(
                        "components.unresolvedBase",
                        f"Cyclic component dependency: {' -> '.join((*ancestry, name))}",
                    )
                raise ValueError(
                    f"Cyclic component dependency: {' -> '.join((*ancestry, name))}"
                )
            for component in layer[name].components:
                if component.baseGlyph in layer:
                    check_cycle(component.baseGlyph, (*ancestry, name))

        for glyph in layer:
            if native:
                from .host import NativeFontBackend, _stage_source

                NativeFontBackend._safe_glyph_name(glyph.name)
                _stage_source(glyph)
            for component in glyph.components:
                if component.baseGlyph not in layer:
                    if native:
                        raise UnsupportedCapability(
                            "components.unresolvedBase",
                            f"Missing component base {component.baseGlyph!r} in {layer.name!r}",
                        )
                    raise ValueError(
                        f"Missing component base {component.baseGlyph!r} in {layer.name!r}"
                    )
            check_cycle(glyph.name)
            yield {"kind": "glyph", "layer": layer.name, "name": glyph.name}
    if native:
        from .fontdata import stage_lib
        from .groups import stage_groups
        from .host import _check_lib
        from .info import stage_info

        stage_info(
            {
                field: deepcopy(getattr(source.info, field))
                for field in INFO_FIELDS
                if getattr(source.info, field) is not None
            },
            "Import UFO info",
        )
        stage_groups(source.groups)
        lib = deepcopy(dict(source.lib))
        lib.pop(BLOCKS_KEY, None)
        stage_lib(lib)
        _check_lib(lib)
        if any(not name.isascii() for name in source.groups):
            raise UnsupportedCapability(
                "ufo.import.groups",
                "Unicode class names cannot survive native persistence",
            )
        for pair, value in source.kerning.items():
            if value != int(value):
                raise UnsupportedCapability(
                    "kerning.fractionalHistory",
                    f"UFO kerning: {pair[0]} {pair[1]} = {value:g} is not a whole "
                    "number; native history rounds fractional values. "
                    "Round that pair first; no changes applied.",
                )
        blocks = source.lib.get(BLOCKS_KEY)
        if blocks is None:
            blocks = split_history_text(source.features.text)
        try:
            staged = stage_blocks(blocks)
        except ValueError as error:
            raise UnsupportedCapability(
                "ufo.import.features.history", str(error)
            ) from error
        if text_from_blocks(staged) != source.features.text:
            raise UnsupportedCapability(
                "ufo.import.features",
                "UFO features cannot be split into byte-equal native blocks",
            )
        if source.features.text:
            from .native_features import _check_languagesystem_prefix

            try:
                _check_languagesystem_prefix(staged["prefix"])
            except ValueError as error:
                raise UnsupportedCapability(
                    "ufo.import.features.languagesystem", str(error)
                ) from error
    yield {"kind": "metadata"}


def import_native(source: Font):
    """Return a context owning a new registered native font, after preflight."""

    def create():
        from .application import NativeApplication
        from .host import NativeFontBackend

        identifier = NativeApplication().new_font(None, None)
        try:
            return NativeFontBackend(identifier, owns_document=True)
        except Exception:
            import fontpr

            fontpr.call("close_font", font_id=identifier, save=False)
            raise

    return import_ufo(source, create, native=True)


def _apply_import(source, backend, font, native):
    default = backend.default_layer()
    values = {
        field: deepcopy(getattr(source.info, field))
        for field in INFO_FIELDS
        if getattr(source.info, field) is not None
    }
    if native:
        # Stem snaps are refused once the document has unsaved history, and
        # glyph writes create history. Write them first, on the fresh owned
        # document, before any other edit.
        stems = {
            field: values.pop(field) for field in sorted(STEM_SNAP_FIELDS & set(values))
        }
        if stems:
            backend.set_info_many(stems, require_single_undo=False)
    for layer in source.layers:
        name = default if layer is source.layers.defaultLayer else layer.name
        if name not in backend.layer_names():
            backend.new_layer(name)
        # Allocate bases before assigning any component references.
        for glyph in layer:
            backend.new_glyph(glyph.name, name)
            yield {"kind": "new", "layer": name, "name": glyph.name}
        for glyph in layer:
            backend.write_glyph(glyph.name, name, glyph)
            yield {"kind": "glyph", "layer": name, "name": glyph.name}
    if values:
        if native:
            # This is a new owned import, not an editor batch. History and
            # legacy-class losses are explicitly listed in this API.
            backend.set_info_many(values, require_single_undo=False)
        else:
            backend.set_info_many(values)
    yield {"kind": "info"}
    for attr in ("groups", "kerning", "lib"):
        values = deepcopy(getattr(source, attr))
        if attr == "lib":
            values.pop(BLOCKS_KEY, None)
        if native and attr == "groups":
            backend.set_groups(values, require_persistence=False)
        else:
            getattr(backend, "set_" + attr)(values)
        yield {"kind": attr}
    if native:
        backend.set_feature_blocks(
            source.lib.get(BLOCKS_KEY) or split_history_text(source.features.text)
        )
    else:
        backend.set_features(source.features.text)
    yield {"kind": "features"}
    font.refresh()


class ImportSession:
    """Detach/preflight one glyph per step before allowing native allocation."""

    def __init__(self, source, *, native=False):
        self.source, self.native = source, native
        self.staged = Font()
        self.staged.layers.renameLayer(
            self.staged.layers.defaultLayer.name, source.layers.defaultLayer.name
        )
        self.staged.info = deepcopy(source.info)
        self.staged.groups = deepcopy(source.groups)
        self.staged.kerning = deepcopy(source.kerning)
        self.staged.features.text = source.features.text
        self.staged.lib = deepcopy(source.lib)
        self.complete = False
        self.allocated = False

    def preflight_steps(self):
        if self.complete:
            raise RuntimeError("Import preflight already completed")
        for layer in self.source.layers:
            target = (
                self.staged.layers[layer.name]
                if layer.name in self.staged.layers
                else self.staged.layers.newLayer(layer.name)
            )
            for glyph in layer:
                target.insertGlyph(deepcopy(glyph), overwrite=False)
                yield {"kind": "detach", "layer": layer.name, "name": glyph.name}
        yield from preflight_import(self.staged, native=self.native)
        self.complete = True
        self.source = None

    def begin(self, backend_factory):
        from .live import RFont

        if not self.complete or self.allocated:
            raise RuntimeError("Exhaust preflight once before allocating a destination")
        backend = backend_factory()
        self.allocated = True
        font = RFont(backend)
        return font, _apply_import(self.staged, backend, font, self.native)


@contextmanager
def import_ufo(source: Font, backend_factory, *, native=False):
    """Own and close a new destination, with all preflight before allocation.

    Outside FontLab this convenience exhausts preflight. Inside run_python use
    ImportSession.preflight_steps()/begin(), one next() per call, and close the
    returned owned font in the controller's finally block.
    """
    session = ImportSession(source, native=native)
    for _ in session.preflight_steps():
        pass
    font, steps = session.begin(backend_factory)
    try:
        yield font, steps
    finally:
        font.close()
