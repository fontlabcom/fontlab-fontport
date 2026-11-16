# this_file: src/fontlab_fontport/application.py
"""Lazy application calls using native fontpr's documented JSON results."""

from .host import NativeFontBackend
from .paths import absolute_path


class NativeApplication:
    """Application boundary used by FontWorld; no native objects are retained."""

    def font_ids(self) -> tuple[int, ...]:
        import fontpr

        return tuple(font["id"] for font in fontpr.call("list_fonts")["fonts"])

    def current_font_id(self) -> int | None:
        if not self.font_ids():
            return None
        import fontpr

        try:
            return fontpr.call("get_active_font")["id"]
        except fontpr.Error as error:
            if str(error) == "No active font.":
                return None
            raise

    def backend(self, identifier: int, *, owned: bool) -> NativeFontBackend:
        return NativeFontBackend(identifier, owns_document=owned)

    def close_font(self, identifier: int) -> None:
        """Discard only an explicitly owned allocation whose wrapper failed."""
        import fontpr

        fontpr.call("close_font", font_id=identifier, save=False)

    def _create(self, tool: str, **parameters) -> int:
        import fontpr

        before = set(self.font_ids())
        fontpr.call(tool, **parameters)
        created = set(self.font_ids()) - before
        if len(created) != 1:
            raise RuntimeError(
                f"{tool} created {len(created)} documents; refusing ambiguous ownership"
            )
        return created.pop()

    def open_font(self, path: str) -> int:
        source = absolute_path(path, strict=True)
        return self._create("open_font", path=str(source))

    def new_font(self, family: str | None, style: str | None) -> int:
        return self._create(
            "new_font",
            family_name="Untitled" if family is None else family,
            style_name="Regular" if style is None else style,
        )
