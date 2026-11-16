# this_file: src/fontlab_fontport/testing.py
"""Upstream FontParts yardstick, with owned fixtures and per-test raw receipts.

FontParts 1.1.x exports testEnvironment from fontParts.test, not fontParts.tests.
No upstream modules or dispatchers are impersonated or replaced.
"""

import contextvars
import unittest
from contextlib import contextmanager
from time import monotonic

from .errors import UnsupportedCapability

_generator = contextvars.ContextVar("fontport_test_generator", default=None)
FAMILIES = (
    "font",
    "info",
    "groups",
    "kerning",
    "features",
    "lib",
    "layer",
    "glyph",
    "contour",
    "segment",
    "bPoint",
    "point",
    "component",
    "anchor",
    "guideline",
    "image",
)


class ObjectGenerator:
    def __init__(self, *, backend_factory=None, fontshell=False, native_attached=False):
        self.backend_factory = backend_factory
        self.fontshell = fontshell
        self.native_attached = native_attached
        self.owned = []
        self.pending_ids = []
        self.families = []

    def __call__(self, cls_name):
        if cls_name not in FAMILIES:
            raise ValueError(f"Unknown FontParts object family: {cls_name}")
        from fontParts.fontshell.test import fontshellObjectGenerator

        from .live import RFont

        detached = self.fontshell or (
            self.backend_factory is not None
            and cls_name != "font"
            and not self.native_attached
        )
        self.families.append(
            {
                "family": cls_name,
                "route": "fontshell-parity"
                if detached
                else "unsupported-native-orphan"
                if self.backend_factory is None
                and cls_name != "font"
                and not self.native_attached
                else "live-attached"
                if self.backend_factory is not None
                and self.native_attached
                and cls_name != "font"
                else "live-font"
                if self.backend_factory
                else "native-owned",
            }
        )
        if detached:
            # Detached-family parity is labelled separately from live-font tests.
            return fontshellObjectGenerator(cls_name)
        if (
            self.backend_factory is None
            and cls_name != "font"
            and not self.native_attached
        ):
            raise UnsupportedCapability(
                f"testing.nativeOrphan.{cls_name}",
                "Upstream requests a detached orphan; this adapter currently binds registered document/glyph owners and does not implement detached native wrappers. Use ObjectGenerator(native_attached=True) for owned integration fixtures; no fake native orphan is returned",
            )
        if self.backend_factory is not None:
            font = RFont(self.backend_factory())
        else:
            from .application import NativeApplication
            from .host import NativeFontBackend

            identifier = NativeApplication().new_font(None, None)
            self.pending_ids.append(identifier)
            font = RFont(NativeFontBackend(identifier, owns_document=True))
        self.owned.append(font)
        if cls_name == "font":
            return font, []
        if cls_name in ("info", "groups", "kerning", "features", "lib"):
            return getattr(font, cls_name), [font]
        if cls_name == "layer":
            return font.defaultLayer, [font]
        glyph = font.newGlyph("fontport_test")
        if cls_name == "glyph":
            return glyph, [font]
        if cls_name == "anchor":
            glyph.appendAnchor("test", (0, 0))
            return glyph.anchors[0], [font, glyph]
        if cls_name == "component":
            font.newGlyph("fontport_base")
            glyph.appendComponent("fontport_base")
            return glyph.components[0], [font, glyph]
        if cls_name == "guideline":
            glyph.appendGuideline((0, 0), 0)
            return glyph.guidelines[0], [font, glyph]
        if cls_name == "image":
            raise UnsupportedCapability(
                "glyph.image", "Native image round-trip is not implemented"
            )
        if cls_name in ("contour", "point", "segment", "bPoint"):
            if cls_name == "contour":
                from defcon import Contour

                model = Contour()
                glyph.naked().appendContour(model)
                return glyph.contours[0], [font, glyph]
            pen = glyph.getPen()
            pen.moveTo((0, 0))
            pen.lineTo((100, 0))
            pen.lineTo((0, 100))
            pen.closePath()
            contour = glyph.contours[0]
            return {
                "contour": contour,
                "point": contour.points[0],
                "segment": contour.segments[0],
                "bPoint": contour.bPoints[0],
            }[cls_name], [font, glyph]
        raise ValueError(f"Unknown FontParts object family: {cls_name}")

    def close(self):
        errors = []
        for font in list(reversed(self.owned)):
            try:
                if not font._closed:
                    font.close()
                self.owned = [item for item in self.owned if item is not font]
                identifier = getattr(font._backend, "font_id", None)
                if identifier in self.pending_ids:
                    self.pending_ids.remove(identifier)
            except Exception as error:  # noqa: BLE001 - retain all cleanup failures
                errors.append(str(error))
        if errors:
            raise RuntimeError("Owned test font cleanup failed: " + "; ".join(errors))


@contextmanager
def generator_context(generator, *, cleanup=True):
    token = _generator.set(generator)
    try:
        yield generator
    finally:
        try:
            if cleanup:
                generator.close()
        finally:
            _generator.reset(token)


def object_generator(cls_name):
    """Upstream callable; use generator_context to deterministically close owners."""
    generator = _generator.get()
    if generator is None:
        raise RuntimeError(
            "Use generator_context(ObjectGenerator()) around upstream tests"
        )
    return generator(cls_name)


def upstream_tests():
    from fontParts import test

    loader = unittest.TestLoader()
    result = []

    def collect(suite):
        for case in suite:
            if isinstance(case, unittest.TestSuite):
                collect(case)
            else:
                result.append(case)

    for name, module in vars(test).items():
        if name.startswith("test_") and hasattr(module, "__file__"):
            collect(loader.loadTestsFromModule(module))
    return sorted(result, key=lambda case: case.id())


class _ReceiptResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.problem_types = []

    def addError(self, test, error):
        self.problem_types.append(error[0])
        super().addError(test, error)

    def addFailure(self, test, error):
        self.problem_types.append(error[0])
        super().addFailure(test, error)

    def addSubTest(self, test, subtest, error):
        if error is not None:
            self.problem_types.append(error[0])
        super().addSubTest(test, subtest, error)


def run_test(case, generator, *, cleanup=True):
    """Never relabel an assertion/unknown error as a native defect or a pass."""
    import sys

    from .testing_exclusions import ATTACHED_PARENT_TESTS

    generator.families = []
    if (
        generator.native_attached
        and not generator.fontshell
        and case.id() in ATTACHED_PARENT_TESTS
    ):
        return {
            "id": case.id(),
            "status": "HarnessExclusion",
            "capability": "testing.nativeAttached.parents",
            "seconds": 0,
            "errors": [
                "testing.nativeAttached.parents: upstream requires an orphan or replaceable parent; this fixture has a fixed owned parent"
            ],
            "skipped": [],
            "fixtures": [],
            "surface": "native-owned-attached",
        }
    result = _ReceiptResult()
    started = monotonic()
    case.objectGenerator = object_generator
    try:
        with generator_context(generator, cleanup=cleanup):
            case.run(result)
    except Exception:  # noqa: BLE001 - preserve cleanup evidence
        result.addError(case, sys.exc_info())
    problems = [trace for _, trace in result.errors + result.failures]
    problems += [
        "Unexpected unittest success: " + item.id()
        for item in result.unexpectedSuccesses
    ]
    status = "pass"
    if problems:
        status = (
            "UnsupportedCapability"
            if result.problem_types
            and not result.unexpectedSuccesses
            and all(
                issubclass(kind, UnsupportedCapability) for kind in result.problem_types
            )
            else "unclassified"
        )
    elif result.skipped:
        status = "upstream-skip"
    elif result.expectedFailures:
        status = "upstream-expected-failure"
    return {
        "id": case.id(),
        "status": status,
        "seconds": monotonic() - started,
        "errors": problems,
        "skipped": [reason for _, reason in result.skipped],
        "fixtures": list(generator.families),
        "surface": "fontshell-parity"
        if generator.fontshell
        else "live-font/detached-orphan-parity"
        if generator.backend_factory
        else "native-owned-attached"
        if generator.native_attached
        else "native-owned",
    }


def main(argv=None):
    """Write receipts from the installed upstream suite without contacting a host."""
    import argparse
    import json
    from collections import Counter
    from pathlib import Path

    from .memory import UFOBackend

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", choices=("fontshell", "memory"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = [
        run_test(
            case,
            ObjectGenerator(
                fontshell=args.surface == "fontshell",
                backend_factory=UFOBackend if args.surface == "memory" else None,
            ),
        )
        for case in upstream_tests()
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row) + "\n" for row in rows))
    print(json.dumps(dict(Counter(row["status"] for row in rows))))
    return int(any(row["status"] == "unclassified" for row in rows))


if __name__ == "__main__":
    raise SystemExit(main())
