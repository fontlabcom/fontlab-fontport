# this_file: src/fontlab_fontport/memory.py
"""Real UFO storage backend for host-free adapter tests and interchange staging.

This is explicitly not a native FontLab backend and claims no native history.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from typing import Any

from ufoLib2 import Font

from .paths import absolute_path

_ANCHOR_FIELDS = ("name", "x", "y", "color", "identifier")
_GUIDE_FIELDS = (*_ANCHOR_FIELDS, "angle")


def _fields(mark, names):
    """Return the UFO fields of an anchor or guideline as a plain dict."""
    return {n: v for n in names if (v := _plain(getattr(mark, n, None))) is not None}


def _plain(value):
    """FontParts exposes colors as tuples; ufoLib2 stores them as strings."""
    if isinstance(value, tuple):
        return ",".join(f"{c:g}" for c in value)
    return value

_IMAGE_DATA_UNSET = object()


def _validate_image_data(data: Any) -> None:
    from fontParts.base.errors import FontPartsError
    from fontTools.ufoLib.validators import pngValidator

    if not isinstance(data, bytes):
        raise FontPartsError("The image data provided is not valid.")
    if not pngValidator(data=data)[0]:
        raise FontPartsError("The image must be in PNG format.")


class UFOBackend:
    glyph_global_fields = ()

    def __init__(self, font=None):
        self.font = Font() if font is None else font
        self.closed = False
        self.saved_path = None

    def check_open(self):
        from .errors import StaleObjectError

        if self.closed:
            raise StaleObjectError("Font is closed")

    def layer_names(self):
        self.check_open()
        return tuple(layer.name for layer in self.font.layers)

    def default_layer(self):
        self.check_open()
        return self.font.layers.defaultLayer.name

    def glyph_names(self, layer):
        self.check_open()
        return tuple(self.font.layers[layer].keys())

    def glyph_summaries(self, layer):
        self.check_open()
        return tuple(
            (glyph.name, tuple(glyph.unicodes), glyph.width) for glyph in self.font.layers[layer]
        )

    def has_glyph(self, name, layer):
        self.check_open()
        return layer in self.font.layers and name in self.font.layers[layer]

    def read_glyph(self, name, layer):
        self.check_open()
        return deepcopy(self.font.layers[layer][name])

    def write_glyph(self, name, layer, source):
        from ufoLib2.objects import Glyph

        self.check_open()
        if hasattr(source, "naked"):
            source = source.naked()
        result = Glyph(
            name,
            width=source.width,
            height=source.height,
            unicodes=list(source.unicodes),
            note=source.note,
            lib=deepcopy(dict(source.lib)),
        )
        source.drawPoints(result.getPointPen())
        # FontParts/defcon marks are not mappings: copy their UFO fields.
        result.anchors = [_fields(a, _ANCHOR_FIELDS) for a in source.anchors]
        result.guidelines = [_fields(g, _GUIDE_FIELDS) for g in source.guidelines]
        result.image = dict(result.image) | deepcopy(dict(source.image))
        self.font.layers[layer].insertGlyph(result, overwrite=True)

    def read_image(self, file_name: str | None) -> bytes | None:
        self.check_open()
        return self.font.images.get(file_name)

    @contextmanager
    def edit_image(
        self, name: str, layer: str, data: Any = _IMAGE_DATA_UNSET
    ) -> Iterator[str | None]:
        """Commit one glyph reference and optional new PNG, or restore both."""
        from fontTools.ufoLib.filenames import userNameToFileName

        self.check_open()
        if data is not _IMAGE_DATA_UNSET:
            _validate_image_data(data)
        original = self.read_glyph(name, layer)
        images = self.font.images
        file_name = None
        added = False
        if data is not _IMAGE_DATA_UNSET:
            file_name = original.image.fileName
            if file_name not in images or images[file_name] != data:
                file_name = next((key for key in images if images[key] == data), None)
            added = file_name is None
            if added:
                file_name = userNameToFileName(
                    "image", existing={key.lower() for key in images}, suffix=".png"
                )
        try:
            if added:
                images[file_name] = data
            yield file_name
        except BaseException as error:
            try:
                self.font.layers[layer].insertGlyph(original, overwrite=True)
                if added and file_name in images:
                    del images[file_name]
            except BaseException as cleanup:
                error.add_note(f"Image rollback failed: {cleanup!r}")
                raise error from cleanup
            raise

    def new_glyph(self, name, layer):
        self.check_open()
        self.font.layers[layer].newGlyph(name)

    def remove_glyph(self, name, layer):
        self.check_open()
        del self.font.layers[layer][name]

    def rename_glyph(self, old, new, layer):
        self.check_open()
        self.font.layers[layer].renameGlyph(old, new)

    def new_layer(self, name, color=None):
        self.check_open()
        self.font.layers.newLayer(name)

    def remove_layer(self, name):
        self.check_open()
        del self.font.layers[name]

    def rename_layer(self, old, new):
        self.check_open()
        self.font.layers.renameLayer(old, new)

    def get_info(self, attr):
        self.check_open()
        return deepcopy(getattr(self.font.info, attr))

    def set_info(self, attr, value, **kwargs):
        self.set_info_many({attr: value}, **kwargs)

    def set_info_many(self, values, **kwargs):
        self.check_open()
        for attr, value in values.items():
            setattr(self.font.info, attr, deepcopy(value))

    def get_groups(self):
        self.check_open()
        return {name: tuple(members) for name, members in self.font.groups.items()}

    def set_groups(self, values, **kwargs):
        self.check_open()
        self.font.groups = deepcopy(dict(values))

    def get_kerning(self):
        self.check_open()
        return dict(self.font.kerning)

    def set_kerning(self, values, **kwargs):
        self.check_open()
        self.font.kerning = dict(values)

    def get_lib(self):
        self.check_open()
        return deepcopy(dict(self.font.lib))

    def set_lib(self, values, **kwargs):
        self.check_open()
        self.font.lib = deepcopy(dict(values))

    def get_features(self):
        self.check_open()
        return self.font.features.text

    def set_features(self, value, **kwargs):
        self.check_open()
        self.font.features.text = value or ""

    def get_feature_blocks(self):
        from .ufo_features import read_blocks

        return read_blocks(self.get_features())

    def set_feature_blocks(self, values, **kwargs):
        from .ufo_features import stage_blocks

        proposed = stage_blocks(self.get_features(), values)
        if proposed is not None:
            self.set_features(proposed, **kwargs)

    def path(self):
        self.check_open()
        return self.saved_path

    def save_options(self, path, *, formatVersion=None, fileStructure=None):
        from .errors import UnsupportedCapability

        self.check_open()
        if formatVersion not in (None, 3):
            raise UnsupportedCapability(
                "font.save.ufoVersion", "ufoLib2 writes UFO 3 only"
            )
        target = absolute_path(path)
        self.font.save(
            target,
            overwrite=True,
            formatVersion=formatVersion or 3,
            structure=fileStructure,
        )
        self.saved_path = str(target)

    def save(self, path, **kwargs):
        self.save_options(path)

    def close(self):
        self.check_open()
        self.closed = True
