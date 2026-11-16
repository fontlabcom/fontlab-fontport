# this_file: tests/test_fontdata.py
"""FontParts feature/lib boundaries, staging and native refusal contracts."""

from copy import deepcopy
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fontParts.base import BaseFeatures, BaseLib
from test_live import Backend

from fontlab_fontport.fontdata import FeatureEdit, stage_lib
from fontlab_fontport.live import RFont


class DataBackend(Backend):
    def __init__(self):
        super().__init__()
        self.text = "# before\r\n"
        self.lib = {"unknown": [1]}
        self.events = []

    def get_features(self):
        return self.text

    def set_features(self, text, *, undo_name):
        self.text = text
        self.events.append(undo_name)

    def get_lib(self):
        return deepcopy(self.lib)

    def set_lib(self, values, *, undo_name):
        self.lib = deepcopy(values)
        self.events.append(undo_name)


def test_features_when_staged_then_apply_revert_and_exact_text():
    backend = DataBackend()
    font = RFont(backend)
    assert isinstance(font.features, BaseFeatures) and font.features.font is font
    edit = FeatureEdit(font.features)
    text = "# Ω\r\nfeature liga { sub f i by fi; } liga;\n\n"
    edit.text = text
    assert edit.dirty and backend.text == "# before\r\n"
    edit.revert()
    assert not edit.dirty and edit.text == backend.text
    edit.text = text
    edit.apply()
    assert backend.text == font.features.text == text and not edit.dirty
    edit.apply()
    assert backend.events == ["FontParts features"], "identical apply adds no edit"
    font.features.text = None
    assert backend.text is None, "upstream distinguishes absent from empty"
    font.close()
    with pytest.raises(RuntimeError, match="closed"):
        edit.apply()


def test_lib_when_full_plist_then_detached_atomic_update_and_clear():
    backend = DataBackend()
    font = RFont(backend)
    assert isinstance(font.lib, BaseLib) and font.lib.font is font
    values = {
        "Ω": {
            "data": b"\x00\xff",
            "date": datetime(2026, 1, 1),  # noqa: DTZ001 - XML plist uses naive UTC dates.
            "array": [True, 1, 2.5, "x&<>"],
        }
    }
    font.lib.update(values)
    assert backend.lib == {"unknown": [1], **values}
    detached = font.lib["Ω"]
    detached["array"].append(100)
    assert font.lib["Ω"]["array"] == [True, 1, 2.5, "x&<>"]
    before = deepcopy(backend.lib)
    with pytest.raises((TypeError, ValueError)):
        font.lib.update({"good": 1, "bad": None})
    assert backend.lib == before and len(backend.events) == 1
    font.lib.apply({"tuple": (1, 2)})
    assert dict(font.lib) == {"tuple": [1, 2]}, (
        "plist serialization canonicalizes arrays"
    )
    del font.lib["tuple"]
    font.lib.clear()
    assert backend.lib == {} and len(backend.events) == 3
    font.close()
    with pytest.raises(RuntimeError, match="closed"):
        _ = font.lib


@pytest.mark.parametrize(
    "value",
    [
        {"bad": None},
        {"bad": float("nan")},
        {"bad": float("inf")},
        {"bad": 2**65},
        {"bad": datetime(2026, 1, 1, microsecond=1)},  # noqa: DTZ001 - probe lossy naive plist dates.
        {"bad": datetime(2026, 1, 1, tzinfo=UTC)},
        {"": 1},
        {"bad": object()},
        {"bad": "control\x01text"},
    ],
)
def test_stage_lib_when_unserializable_then_refused(value):
    with pytest.raises((TypeError, ValueError, OverflowError)):
        stage_lib(value)


def test_native_font_lib_when_validated_then_preserves_unknown_and_history(monkeypatch):
    from fontlab_fontport.host import NativeFontBackend

    events = []
    package = SimpleNamespace(
        packageLib={"unknown": [1]},
        mastersContainer=lambda: "masters",
        checkInitHistoryState=lambda index: events.append(index),
    )
    backend = object.__new__(NativeFontBackend)
    backend._package = lambda: package
    import sys

    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flItems=SimpleNamespace(
                notifyChangesApplied=lambda title, objects: events.append(
                    (title, objects)
                )
            )
        ),
    )
    font = RFont(backend)
    font.lib["Ω"] = {"text": "x&<>\n", "zero": 0}
    assert package.packageLib == {"unknown": [1], "Ω": {"text": "x&<>\n", "zero": 0}}
    before = deepcopy(package.packageLib), list(events)
    with pytest.raises(NotImplementedError, match="JSON"):
        font.lib["binary"] = b"data"
    assert (package.packageLib, events) == before


def test_feature_edit_when_real_fontparts_saved_then_ufo_interop_and_newline_boundary(
    tmp_path,
):
    from fontParts.fontshell import RFont as ShellFont
    from ufoLib2 import Font

    font = ShellFont()
    edit = FeatureEdit(font.features)
    text = "# Ω\r\nfeature liga { sub f i by fi; } liga;\n"
    edit.text = text
    edit.apply()
    assert font.features.text == text and not edit.dirty
    font.lib.update(
        stage_lib(
            {
                "data": b"\x00\xff",
                "date": datetime(2026, 1, 1),  # noqa: DTZ001 - XML plist uses naive UTC dates.
                "unknown": {"values": [True, 1, "Ω & <>"]},
            }
        )
    )
    path = tmp_path / "features.ufo"
    font.save(str(path))
    assert (path / "features.fea").read_bytes() == text.encode("utf-8")
    with Font.open(path) as reopened:
        # fontTools' UFOReader opens in universal-newline mode. Record this
        # upstream boundary explicitly, rather than claiming exact CRLF reload.
        assert reopened.features.text == text.replace("\r\n", "\n")
        assert reopened.lib["data"] == b"\x00\xff"
        assert reopened.lib["date"] == datetime(2026, 1, 1)  # noqa: DTZ001 - plist dates reopen as naive UTC.
        assert reopened.lib["unknown"] == {"values": [True, 1, "Ω & <>"]}
