# this_file: src/fontlab_fontport/errors.py
"""Explicit capability boundaries, compatible with NotImplementedError callers."""


class StaleObjectError(RuntimeError):
    """A document, layer or glyph binding no longer identifies a live object."""


class UnsupportedCapability(NotImplementedError):
    """A requested contract has no supported native implementation."""

    def __init__(
        self, capability: str, reason: str, *, checked_apis: tuple[str, ...] = ()
    ):
        if not isinstance(capability, str) or not capability.strip():
            raise ValueError(
                "UnsupportedCapability requires a nonempty capability name"
            )
        self.capability = capability
        self.checked_apis = checked_apis
        checked = f" Checked: {', '.join(checked_apis)}." if checked_apis else ""
        super().__init__(f"{capability}: {reason}{checked}")
