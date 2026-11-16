# this_file: Scripts/Features/Feature Parser Demo.py
# SPDX-License-Identifier: Apache-2.0
"""Feature Parser Demo.

What: Parse a small ligature feature with an explicit detached glyph-name set.
Use: Run from FontLab's Scripts menu to open a read-only snapshot report.
Safety: Uses detached sample data only; no font, history, selection, preferences,
Output or clipboard is changed. No open font is required.
"""


def build_report() -> dict:
    """Return real package results without importing a native host or opening UI."""
    from fly.fp.recipes import parse_features

    source = "feature liga { sub f i by f_i; } liga;"
    parsed = parse_features(source, ["f", "i", "f_i"])
    return {
        "source": source,
        "parsed": parsed.asFea(),
        "block_count": len(parsed.statements),
    }


def main() -> None:
    """Show the results using Fly and App's existing nonmodal report window."""
    from fly.ap.proof.reports.model import show_report

    show_report(
        build_report(),
        title="Feature Parser Demo",
        key="fontlab-fontport-feature-parser-demo",
    )


if __name__ == "__main__":
    main()
