# this_file: src/fontlab_fontport/designspace_io.py
"""Export a multi-master font as a ``.designspace`` plus one UFO per master.

MVP, built on the whole-font UFO export: each native master is a layer of the
exported UFO (see ``interchange.ExportSession``), so this splits those layers
into one UFO per master and writes axes, sources and instances with fontTools.
Kerning is read per master (``flPackage.kerning(master)``) and written to each
master UFO. Info, groups, lib and features are shared by every master UFO
because the native adapter reads only the key master's. ``losses`` names what
is not carried (rules, labels, per-master groups, brace layers).
Importing a ``.designspace`` into FontLab is not provided: native master
creation is unavailable (see docs/UFO-INTERCHANGE.md).
"""

import re
from copy import deepcopy
from pathlib import Path

from fontTools.designspaceLib import DesignSpaceDocument
from ufoLib2 import Font

from .designspace import Designspace
from .interchange import ExportSession
from .paths import absolute_path

LOSSES = (
    "designspace.rules: native rules are not read",
    "designspace.labels: axis and location labels are not read",
    "designspace.masterData: groups, info, lib and features come from the key master only and are shared by every master UFO",
    "designspace.instances: instances are listed without generated UFOs",
)


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-") or "master"


def write_designspace(
    font: Font,
    document: DesignSpaceDocument,
    destination: str | Path,
    master_kerning: dict | None = None,
) -> Path:
    """Write ``destination`` (.designspace) and ``<stem>-<master>.ufo`` beside it.

    ``master_kerning`` maps source names to their own kerning; sources missing
    from it get ``font.kerning``.
    Every source name must be a layer of ``font``. Nothing is overwritten and
    ``document`` is not modified. Returns the designspace path.
    """
    target = absolute_path(destination)
    if target.suffix.lower() != ".designspace":
        raise ValueError("Destination must end in .designspace")
    if not document.sources:
        raise ValueError("The designspace has no sources")
    missing = [s.name for s in document.sources if s.name not in font.layers]
    if missing:
        raise ValueError(f"Sources without a master layer: {missing}")
    doc = deepcopy(document)
    files = {}
    for source in doc.sources:
        name = f"{target.stem}-{_slug(source.name)}.ufo"
        if name in files.values():
            raise ValueError(f"Source names collide as file names: {source.name}")
        files[source.name] = name
    paths = [target.with_name(name) for name in files.values()]
    for path in (target, *paths):
        if path.exists():
            raise FileExistsError(path)
    for source in doc.sources:
        ufo = Font()
        for glyph in font.layers[source.name]:
            ufo.layers.defaultLayer.insertGlyph(glyph, overwrite=False)
        ufo.info = deepcopy(font.info)
        ufo.groups = deepcopy(font.groups)
        ufo.kerning = deepcopy((master_kerning or {}).get(source.name, font.kerning))
        ufo.lib = deepcopy(font.lib)
        ufo.features.text = font.features.text
        ufo.info.styleName = source.styleName or source.name
        path = target.with_name(files[source.name])
        ufo.save(path)
        source.filename = path.name
        source.path = str(path)
        source.familyName = source.familyName or font.info.familyName
        source.styleName = source.styleName or source.name
    for instance in doc.instances:
        instance.filename = None
        instance.path = None
    doc.write(target)
    return target


def export_designspace(
    backend, destination: str | Path, document: DesignSpaceDocument | None = None
) -> tuple[Path, list[str]]:
    """Export a backend's masters to ``destination``; return the path and losses.

    Without ``document`` the axes, master locations and instances come from
    ``Designspace.from_native(backend)`` (native package). The borrowed backend
    is only read.
    """
    session = ExportSession(backend)
    for _ in session.steps():
        pass
    if document is None:
        document = Designspace.from_native(backend).document
    path = write_designspace(
        session.font, document, destination, session.master_kerning
    )
    return path, [*session.losses, *LOSSES]
