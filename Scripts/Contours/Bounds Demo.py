# this_file: Scripts/Contours/Bounds Demo.py
# SPDX-License-Identifier: Apache-2.0
"""Bounds Demo.

What: Compare Fontport bounds and control bounds on an owned detached cubic glyph.
Use: Run from FontLab's Scripts menu to open a read-only snapshot report.
Safety: Uses detached sample data only; no font, history, selection, preferences,
Output or clipboard is changed. No open font is required.
"""


def build_report() -> dict:
    """Return real package results without importing a native host or opening UI."""
    from fly.fp.recipes import bounds, control_bounds
    from fontParts.fontshell import RGlyph

    glyph = RGlyph()
    pen = glyph.getPen()
    pen.moveTo((0, 0))
    pen.curveTo((0, 100), (100, 100), (100, 0))
    pen.closePath()
    return {
        "bounds": bounds(glyph),
        "control_bounds": control_bounds(glyph),
        "contours": len(glyph),
    }


def main() -> None:
    """Show the results using Fly and App's existing nonmodal report window."""
    from fly.ap.proof.reports.model import show_report

    show_report(build_report(), title="Bounds Demo", key="fontlab-fontport-bounds-demo")


if __name__ == "__main__":
    main()
