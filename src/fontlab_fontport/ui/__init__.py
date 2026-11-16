# this_file: src/fontlab_fontport/ui/__init__.py
"""Removed FontLab editors: use matching names in ``fontlabapp.fontui``.

Factory/attribute imports and old submodule imports raise migration errors.
This tombstone loads neither App, Qt nor Fontport's editor dependencies.
Fontport has no UI; delete this package in the next release (issue 201).

Migrate: ``from fontlab_fontport.ui import kerning_editor`` becomes
``from fly.ap.fontui import kerning_editor``. The editors need Fontport;
install it with ``pip install "fontlab-fontlabapp[fontport]"``.
"""

import sys
from typing import Any

MOVED_HOME = "fontlabapp.fontui"
#: Removed factory functions (from-import and attribute read only).
_MOVED_FACTORIES = frozenset(
    {
        "font_info_editor",
        "groups_editor",
        "kerning_editor",
        "transform_editor",
        "batch_panel",
        "glyph_sequence",
    }
)
#: Removed modules (also ``import fontlab_fontport.ui.<name>``, via the finder).
_MOVED_MODULES = frozenset(
    {
        "fontinfo",
        "groups",
        "groups_view",
        "kerning",
        "kerning_view",
        "transform",
        "transform_view",
        "batch",
        "batch_worker",
        "sequence",
    }
)
#: Every removed name. Delete in the release after the move. Not in ``__all__``.
MOVED = _MOVED_FACTORIES | _MOVED_MODULES


__all__ = []
_FINDER_MARK = "_fontlab_fontport_ui_tombstone"


def _moved_message(name: str) -> str:
    """Name the corresponding App factory or module."""
    return f"fontlab_fontport.ui.{name} moved to {MOVED_HOME}.{name}"


def __getattr__(name: str) -> Any:
    """Refuse moved attributes; retain normal missing-attribute semantics."""
    if name in MOVED:
        raise ImportError(_moved_message(name))
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


class _MovedModuleFinder:
    """Refuse exact old module names after ordinary file finders miss."""

    _fontlab_fontport_ui_tombstone = True

    @staticmethod
    def find_spec(fullname: str, path: Any = None, target: Any = None) -> None:
        """Raise a migration error only for a removed submodule."""
        package, _, name = fullname.rpartition(".")
        if package == __name__ and name in _MOVED_MODULES:
            raise ImportError(_moved_message(name), name=fullname)


def _install_moved_finder() -> None:
    """Keep exactly one finder across FontLab module purges/reloads."""
    if not any(getattr(finder, _FINDER_MARK, False) for finder in sys.meta_path):
        sys.meta_path.append(_MovedModuleFinder())


_install_moved_finder()
