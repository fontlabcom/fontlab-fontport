# this_file: Scripts/Kerning/Kerning Values Demo.py
# SPDX-License-Identifier: Apache-2.0
"""Kerning Values Demo.

What: Stage explicit kerning pairs, preserving zero and fractional values.
Use: Run from FontLab's Scripts menu to open a read-only snapshot report.
Safety: Uses detached sample data only; no font, history, selection, preferences,
Output or clipboard is changed. No open font is required.
"""


def build_report() -> dict:
    """Return real package results without importing a native host or opening UI."""
    from fly.fp.kerning import stage_kerning

    staged = stage_kerning({("A", "V"): -80, ("T", "o"): 0, ("V", "a"): -12.5})
    return {
        "pairs": [
            {"left": left, "right": right, "value": value}
            for (left, right), value in staged.items()
        ],
        "missing_pair_is_absent": ("A", "o") not in staged,
    }


def main() -> None:
    """Show the results using Fly and App's existing nonmodal report window."""
    from fly.ap.proof.reports.model import show_report

    show_report(
        build_report(),
        title="Kerning Values Demo",
        key="fontlab-fontport-kerning-values-demo",
    )


if __name__ == "__main__":
    main()
