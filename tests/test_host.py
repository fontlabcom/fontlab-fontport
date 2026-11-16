# this_file: tests/test_host.py
"""Native boundary validation without loading FontLab in the test process."""

import sys
from types import SimpleNamespace

import pytest
from ufoLib2.objects import Glyph

from fontlab_fontport.host import NativeFontBackend, _stage_source


def test_native_backend_declares_glyph_global_metadata_without_native_imports():
    assert NativeFontBackend.glyph_global_fields == ("unicodes", "note", "lib"), (
        "FontLab metadata must synchronize across cached layer glyphs"
    )


def test_staging_rejects_fractional_anchors_before_native_import():
    g = Glyph("A", width=500)
    g.appendAnchor({"name": "top", "x": 1.5, "y": 2})
    with pytest.raises(NotImplementedError, match="fractional"):
        _stage_source(g)


def test_staging_detaches_and_validates_plist_and_metrics():
    g = Glyph("A", width=500, lib={"nested": {"values": [1, 2]}})
    source = _stage_source(g)
    source.lib["nested"]["values"].append(3)
    assert g.lib["nested"]["values"] == [1, 2]
    g.width = float("nan")
    with pytest.raises(ValueError, match="finite"):
        _stage_source(g)


def test_backend_reacquires_package_and_detects_external_close(monkeypatch):
    pkg = SimpleNamespace(isNull=False, id=5)
    calls = []

    class Workspace:
        def findPackageId(self, identifier):
            calls.append(identifier)
            return pkg

    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(flWorkspace=SimpleNamespace(instance=lambda: Workspace())),
    )
    b = NativeFontBackend(5)
    assert b._package() is pkg
    assert calls == [5, 5]
    pkg.isNull = True
    with pytest.raises(RuntimeError, match="closed"):
        b.path()


def test_borrowed_close_does_not_close_native_document(monkeypatch):
    pkg = SimpleNamespace(isNull=False, id=5)
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flWorkspace=SimpleNamespace(
                instance=lambda: SimpleNamespace(findPackageId=lambda _: pkg)
            )
        ),
    )
    b = NativeFontBackend(5)
    b.close()
    with pytest.raises(RuntimeError, match="closed"):
        b._package()


def test_unsupported_info_and_save_format_fail_before_mutation(monkeypatch):
    pkg = SimpleNamespace(isNull=False, id=5)
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flWorkspace=SimpleNamespace(
                instance=lambda: SimpleNamespace(findPackageId=lambda _: pkg)
            )
        ),
    )
    b = NativeFontBackend(5)
    with pytest.raises(NotImplementedError):
        b.set_info("unsupported", 1)
    with pytest.raises(NotImplementedError, match="vfj"):
        b.save("/tmp/font.ufo")


@pytest.mark.parametrize("value", [b"binary", 2**54, float("nan")])
def test_staging_refuses_lib_values_that_native_vfj_cannot_retain(value):
    g = Glyph("A", lib={"unsupported": value})
    with pytest.raises((NotImplementedError, ValueError)):
        _stage_source(g)


def test_failed_owned_close_keeps_binding_usable(monkeypatch):
    pkg = SimpleNamespace(isNull=False, id=5, path="/tmp/owned.vfj")
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flWorkspace=SimpleNamespace(
                instance=lambda: SimpleNamespace(findPackageId=lambda _: pkg)
            )
        ),
    )

    def fail(*args, **kwargs):
        raise OSError("close failed")

    monkeypatch.setitem(sys.modules, "fontpr", SimpleNamespace(call=fail))
    b = NativeFontBackend(5, owns_document=True)
    with pytest.raises(OSError, match="close failed"):
        b.close()
    assert b.path() == "/tmp/owned.vfj", "a failed close must retain the live binding"


@pytest.mark.parametrize("stale", ["external_close", "binding_close"])
def test_capabilities_when_document_closed_then_returns_static_table(
    monkeypatch, stale
):
    """capabilities() is static metadata; it must not require a live document."""
    from fontlab_fontport.capabilities import NATIVE_CAPABILITIES
    from fontlab_fontport.live import RFont

    pkg = SimpleNamespace(isNull=False, id=5)
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flWorkspace=SimpleNamespace(
                instance=lambda: SimpleNamespace(findPackageId=lambda _: pkg)
            )
        ),
    )
    b = NativeFontBackend(5)
    if stale == "external_close":
        pkg.isNull = True
    else:
        b.close()
    with pytest.raises(RuntimeError, match="closed"):
        b._package()
    caps = b.capabilities()
    assert caps == NATIVE_CAPABILITIES, "closed host must still report its table"
    caps["glyph.exactSingleUndo"]["supported"] = True
    assert b.capabilities() == NATIVE_CAPABILITIES, "callers get a detached copy"
    assert RFont(b).capabilities() == NATIVE_CAPABILITIES
