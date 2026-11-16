# this_file: src/fontlab_fontport/native_import.py
"""Open a UFO or a ``.designspace`` in FontLab through the native opener.

Thin wrappers over ``NativeApplication.open_font``, which calls the MCP tool
``fontpr.call("open_font", path=...)`` that FontLab itself uses. Native checks
(issue 201, task 17): a ``.ufo`` opens as one font with one master; a
``.designspace`` with one axis and two sources opens as one font with both
masters and the axis. Kerning and anchor import through this route are not
verified yet. Nothing is converted here, so no Fontport loss list applies; the
caller owns the returned backend and must close it.
"""

from pathlib import Path

from .application import NativeApplication
from .host import NativeFontBackend
from .paths import absolute_path


def _open(path: str | Path, suffix: str, application) -> NativeFontBackend:
    source = absolute_path(path)
    if source.suffix.lower() != suffix:
        raise ValueError(f"Source must end in {suffix}")
    if not source.exists():
        raise FileNotFoundError(source)
    if (suffix == ".ufo") != source.is_dir():
        raise ValueError(
            "A .ufo is a directory" if suffix == ".ufo" else "A .designspace is a file"
        )
    app = NativeApplication() if application is None else application
    return app.backend(app.open_font(str(source)), owned=True)


def import_ufo_native(path: str | Path, application=None) -> NativeFontBackend:
    """Open ``path`` (.ufo directory) as a new owned FontLab document."""
    return _open(path, ".ufo", application)


def import_designspace(path: str | Path, application=None) -> NativeFontBackend:
    """Open ``path`` (.designspace) with its source UFOs as one owned document.

    The source UFOs must exist where the designspace points; FontLab, not this
    function, resolves them. Close the result with ``backend.close()``.
    """
    return _open(path, ".designspace", application)
