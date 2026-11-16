# this_file: tests/test_fontparts_examples.py
"""Original scripts run through actual world callbacks with a real UFO backend."""

import importlib
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

from fontlab_fontport.memory import UFOBackend
from fontlab_fontport.world import FontWorld, register


def test_original_examples_run_through_world_on_owned_ufo(monkeypatch):
    from test_interchange import source_font
    from test_world import Host

    root = Path(__file__).resolve().parents[1] / "examples/fontparts"
    monkeypatch.syspath_prepend(str(root))
    backend = UFOBackend(source_font())
    backend.owns_document = True
    backend.set_features(
        "languagesystem DFLT dflt;\nfeature liga { sub A A by V; } liga;\n"
    )
    for name in ("fontport_probe", "fontport_component", "fontport_flat"):
        backend.new_glyph(name, backend.default_layer())
    host = Host()
    host.backends = {1: backend}
    with register(FontWorld(host)):
        scripts = sorted(root.glob("[0-9]*.py"))
        assert len(scripts) == 19
        edits = 0
        for script in scripts:
            receipt = importlib.import_module(script.stem).run()
            assert receipt["ok"], (script.name, receipt)
            if script.name[:2] not in ("11", "13", "14", "16"):
                assert receipt["before"] != receipt["after"], (script.name, receipt)
                edits += 1
        assert edits >= 15


def test_examples_when_fly_imports_then_same_canonical_providers():
    for name in ("errors", "host", "kerning", "live", "recipes"):
        assert importlib.import_module(f"fly.fp.{name}") is importlib.import_module(
            f"fontlab_fontport.{name}"
        )


def test_owned_example_when_no_owned_font_then_refuses(monkeypatch):
    root = Path(__file__).resolve().parents[1] / "examples/fontparts"
    monkeypatch.syspath_prepend(str(root))
    module = importlib.import_module("_owned")
    monkeypatch.setattr(module, "CurrentFont", lambda: None)
    with pytest.raises(NotImplementedError, match=r"examples\.ownership"):
        module.owned()
    with pytest.raises(NotImplementedError, match=r"examples\.ownership"):
        module.owned(SimpleNamespace(_backend=SimpleNamespace(owns_document=False)))


def test_live_example_when_called_then_preserves_requested_edit_and_save(monkeypatch):
    from fontlab_fontport import host, live

    glyph = SimpleNamespace(width=500, note="", lib={})
    calls = []

    class Font(dict):
        def save(self, destination):
            calls.append(("save", destination))

        def close(self):
            calls.append(("close",))

    font = Font(A=glyph)
    monkeypatch.setattr(host, "NativeFontBackend", lambda *a, **kw: calls.append((a, kw)))
    monkeypatch.setattr(live, "RFont", lambda backend: font)
    root = Path(__file__).resolve().parents[1]
    namespace = runpy.run_path(str(root / "examples/live_font.py"))
    namespace["edit_owned_fixture"](42, "/owned/result.vfj")
    assert glyph.width == 650 and glyph.note == "Edited through FontParts"
    assert glyph.lib == {"example": {"text": "owned fixture"}}
    assert calls == [((42,), {"owns_document": True}), ("save", "/owned/result.vfj"), ("close",)]


@pytest.mark.parametrize(
    ("script", "capability"),
    [("13_layers", "layer.create"), ("16_guidelines", "glyph.guidelines")],
)
def test_examples_when_native_capability_refused_then_preserve_data(
    script, capability, monkeypatch
):
    from fontlab_fontport.errors import UnsupportedCapability

    root = Path(__file__).resolve().parents[1] / "examples/fontparts"
    monkeypatch.syspath_prepend(str(root))

    def refuse(*args, **kwargs):
        raise UnsupportedCapability(capability, "fixture refusal")

    class Font(dict):
        _backend = SimpleNamespace(owns_document=True)
        layerOrder = ("public.default",)
        newLayer = staticmethod(refuse)

    font = Font(fontport_probe=SimpleNamespace(guidelines=[], appendGuideline=refuse))
    receipt = importlib.import_module(script).run(font)
    assert receipt["ok"] and receipt["capability"] == capability
    assert receipt["before"] == receipt["after"]


def test_feature_example_when_no_stored_features_then_refuses(monkeypatch):
    root = Path(__file__).resolve().parents[1] / "examples/fontparts"
    monkeypatch.syspath_prepend(str(root))
    font = SimpleNamespace(
        _backend=SimpleNamespace(owns_document=True),
        features=SimpleNamespace(get_blocks=lambda: {"features": []}),
    )
    with pytest.raises(NotImplementedError, match=r"examples\.features"):
        importlib.import_module("12_feature_edit").run(font)
