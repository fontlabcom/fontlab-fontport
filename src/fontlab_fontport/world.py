# this_file: src/fontlab_fontport/world.py
"""Explicit FontParts world integration; importing never changes dispatchers."""

from typing import Any

from fontParts.world import BaseFontList

from .errors import UnsupportedCapability
from .info import _text
from .live import RFont
from .paths import absolute_path


class FontWorld:
    """Stable document handles over an application boundary.

    Existing documents are borrowed. Only documents created/opened through this
    object are owned. External closures invalidate cached handles on refresh.
    Call refresh after native edits/Undo to invalidate loaded glyph snapshots.
    """

    def __init__(self, application: Any = None) -> None:
        if application is None:
            from .application import NativeApplication

            application = NativeApplication()
        self.application = application
        self._fonts: dict[int, RFont] = {}

    def _font(self, identifier: int, *, owned: bool = False) -> RFont:
        font = self._fonts.get(identifier)
        if owned and font is not None and not font._closed:
            font._invalidate()
            font._closed = True
        if font is None or font._closed:
            try:
                font = RFont(self.application.backend(identifier, owned=owned))
            except Exception:
                if owned and hasattr(self.application, "close_font"):
                    self.application.close_font(identifier)
                raise
            self._fonts[identifier] = font
        return font

    def AllFonts(self) -> BaseFontList:
        identifiers = self.application.font_ids()
        for identifier in set(self._fonts) - set(identifiers):
            font = self._fonts.pop(identifier)
            if not font._closed:
                font._invalidate()
                font._closed = True
        return BaseFontList(self._font(identifier) for identifier in identifiers)

    def CurrentFont(self) -> RFont | None:
        self.AllFonts()
        identifier = self.application.current_font_id()
        return None if identifier is None else self._font(identifier)

    def OpenFont(self, path: str, showInterface: bool = True) -> RFont:
        if not showInterface:
            raise UnsupportedCapability(
                "world.OpenFont.hidden", "Native open requires showInterface=True"
            )
        _text(path, "path")
        return self._font(
            self.application.open_font(str(absolute_path(path))), owned=True
        )

    def NewFont(
        self,
        familyName: str | None = None,
        styleName: str | None = None,
        showInterface: bool = True,
    ) -> RFont:
        if not showInterface:
            raise UnsupportedCapability(
                "world.NewFont.hidden", "Native creation requires showInterface=True"
            )
        for field, value in (("familyName", familyName), ("styleName", styleName)):
            if value is not None:
                _text(value, field)
        identifier = self.application.new_font(familyName, styleName)
        return self._font(identifier, owned=True)

    def refresh(self) -> BaseFontList:
        fonts = self.AllFonts()
        for font in fonts:
            font.refresh()
        return fonts


def _install(environment):
    """Register real upstream dispatcher callbacks, returning prior values.

    Use as a context manager on the host thread. Nested contexts restore the
    previous environment. No namespace is replaced and no document is closed.
    Selection dispatch remains unsupported rather than returning fake state.
    """
    from fontParts import world

    def unsupported_selection():
        raise UnsupportedCapability(
            "world.selection", "Native FontParts selection dispatch is unavailable"
        )

    def open_font(pathOrObject, showInterface=True):
        return environment.OpenFont(pathOrObject, showInterface=showInterface)

    def font_constructor(pathOrObject=None, showInterface=True):
        if pathOrObject is None:
            return environment.NewFont(showInterface=showInterface)
        if isinstance(pathOrObject, RFont):
            pathOrObject._check()
            return pathOrObject
        return open_font(pathOrObject, showInterface)

    entries = {
        name: getattr(environment, name)
        for name in ("AllFonts", "CurrentFont", "OpenFont", "NewFont")
    }
    entries["OpenFont"] = open_font
    entries["RFont"] = font_constructor
    entries["OpenFontsFileExtensions"] = lambda: (
        ".vfj",
        ".vfc",
        ".ufo",
        ".otf",
        ".ttf",
    )
    for name in (
        "CurrentGlyph",
        "CurrentLayer",
        "CurrentContours",
        "CurrentSegments",
        "CurrentPoints",
        "CurrentComponents",
        "CurrentAnchors",
        "CurrentGuidelines",
    ):
        entries[name] = unsupported_selection
    # The upstream dispatcher has no unregister/get-optional API. Preserve its
    # registry values (including None) so a context can restore all prior state.
    missing = object()
    previous = {name: world.dispatcher._registry.get(name, missing) for name in entries}
    for name, callback in entries.items():
        world.dispatcher[name] = callback
    return previous, missing


_registrations = []


class Registration:
    """Explicit session registration; close/unregister restores exact callbacks."""

    def __init__(self, environment):
        self.environment = environment
        self.previous, self.missing = _install(environment)
        self.active = True
        _registrations.append(self)

    def __enter__(self):
        return self.environment

    def __exit__(self, *exception):
        self.close()

    def close(self):
        if not self.active:
            return
        if _registrations[-1] is not self:
            raise RuntimeError(
                "Unregister nested FontParts environments in reverse order"
            )
        from fontParts import world

        for name, callback in self.previous.items():
            if callback is self.missing:
                world.dispatcher._registry.pop(name, None)
            else:
                world.dispatcher[name] = callback
        _registrations.pop()
        self.active = False


def register(environment: FontWorld | None = None) -> Registration:
    """Install persistently now, or use as a restoring context manager.

    Importing Fontport alone changes no dispatchers. Existing documents stay
    borrowed; unregister restores callbacks and never closes user documents.
    """
    return Registration(FontWorld() if environment is None else environment)


def unregister() -> None:
    """Undo the most recent registration, harmless when already unregistered."""
    if _registrations:
        _registrations[-1].close()
