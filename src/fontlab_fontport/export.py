# this_file: src/fontlab_fontport/export.py
"""Read a geometry subset into UFO; compile it externally with real ufo2ft.

This is a selected-layer geometry export, not complete native-font conversion.
Native hints, images, application state and feature programs are not exported.
The supplied backend/document is borrowed and is never edited or closed.
"""

from collections.abc import Iterable
from math import isfinite
from pathlib import Path

from ufoLib2 import Font

from .backend import FontBackend
from .groups import _text
from .paths import absolute_path


def _destination(path: str | Path, suffix: str) -> Path:
    target = absolute_path(path)
    if target.suffix.lower() != suffix:
        raise ValueError(f"Destination must end in {suffix}")
    if target.exists():
        raise FileExistsError(target)
    return target


def export_ufo_subset(
    backend: FontBackend,
    names: Iterable[str],
    destination: str | Path,
    *,
    family_name: str,
    license_text: str | None = None,
    source_url: str | None = None,
) -> Path:
    """Export selected glyphs plus all component dependencies, without overwrite.

    Supply a deliberate output family name. Preserve the source copyright and
    optionally include its licence text and public provenance URL. The caller
    chooses the output identity; this function does not clear reserved names.
    """
    target = _destination(destination, ".ufo")
    if not _text(family_name).strip():
        raise ValueError("Output family name must not be blank")
    if isinstance(names, str):
        raise TypeError("Supply a collection of glyph names")
    names = list(dict.fromkeys(names))
    if not names:
        raise ValueError("Choose at least one glyph")
    for name in names:
        _text(name)
    if license_text is not None and not isinstance(license_text, str):
        raise TypeError("Licence text must be a string")
    if source_url is not None:
        _text(source_url)
    layer = backend.default_layer()
    available = set(backend.glyph_names(layer))
    font = Font()

    def load(name: str, ancestry: tuple[str, ...] = ()) -> None:
        if name in ancestry:
            raise ValueError(f"Cyclic component dependency: {name}")
        if name in font:
            return
        if name not in available:
            raise KeyError(name)
        glyph = backend.read_glyph(name, layer)
        if not isfinite(glyph.width):
            raise ValueError(f"Nonfinite glyph width: {name}")
        for component in glyph.components:
            load(component.baseGlyph, (*ancestry, name))
        font.layers.defaultLayer.insertGlyph(glyph, overwrite=False)

    if ".notdef" in available:
        load(".notdef")
    for name in names:
        load(name)
    font.info.familyName, font.info.styleName = family_name, "Regular"
    font.info.unitsPerEm = backend.get_info("unitsPerEm")
    font.info.copyright = backend.get_info("copyright")
    font.info.openTypeNameLicense = license_text
    if source_url is not None:
        font.lib["org.fontlab.fontport.sourceURL"] = source_url
    font.glyphOrder = list(font.keys())
    target.parent.mkdir(parents=True, exist_ok=True)
    font.save(target)
    return target


def compile_ttf(source: str | Path, destination: str | Path) -> Path:
    """Compile a saved UFO externally; native FontLab's five-second limit applies.

    Uses upstream ufo2ft's default cubic-to-quadratic conversion (1/1000 UPM
    maximum conversion error), without claiming native hints or source features.
    """
    target = _destination(destination, ".ttf")
    source = absolute_path(source, strict=True)
    try:
        from ufo2ft import compileTTF
    except ModuleNotFoundError as error:
        if error.name == "ufo2ft":
            raise RuntimeError(
                "Install fontlab-fontport[fontbuild] for TTF compilation"
            ) from error
        raise
    with Font.open(source) as font:
        binary = compileTTF(font)
        target.parent.mkdir(parents=True, exist_ok=True)
        binary.save(target)
    return target
