# this_file: tests/test_native_features.py
"""VFJ-canonical structured features, ordered native calls and history boundaries."""

import sys
from copy import deepcopy
from types import SimpleNamespace

import pytest

from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.host import NativeFontBackend
from fontlab_fontport.live import RFont


@pytest.fixture
def native_features(monkeypatch):
    events = []
    data = {
        "openTypeFeatures": [
            {"feature": "languagesystem DFLT dflt;\r\n@inPrefix = [A];\r\n"},
            {"name": "kern", "feature": "feature kern { pos A V -10; } kern;\r\n"},
            {"name": "liga", "feature": "feature liga {} liga;\n# Ω\n"},
        ],
        "classes": [{"name": "panelOnly", "names": ["A"], "openType": True}],
    }

    class Layout:
        def get_prefix(self):
            raise AssertionError("must not synthesize panel classes")

        def keys(self):
            raise AssertionError("must not decompile binary features")

        def clear(self):
            events.append("clear")
            data["openTypeFeatures"] = []

        def set_prefix(self, text):
            events.append(("prefix", text))
            if text:
                data["openTypeFeatures"].append({"feature": text})

        def set_feature(self, tag, text):
            events.append((tag, text))
            data["openTypeFeatures"].append({"name": tag, "feature": text})

    package = SimpleNamespace(
        fgPackage=SimpleNamespace(features=Layout()),
        checkInitHistoryState=lambda ix: events.append(("init", ix)),
        featuresContainer=lambda: "features-container",
    )
    backend = object.__new__(NativeFontBackend)
    backend.font_id = 42
    backend._package = lambda: package
    monkeypatch.setitem(
        sys.modules,
        "fontpr",
        SimpleNamespace(
            available=lambda: True,
            get_font_info=lambda **kw: (
                deepcopy(data) if kw == {"font_id": 42} else pytest.fail("wrong id")
            ),
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "fontlab",
        SimpleNamespace(
            flItems=SimpleNamespace(
                notifyChangesApplied=lambda name, objects: events.append(
                    (name, objects)
                ),
                notifyFeaturesChanged=lambda ident, binary: events.append(
                    ("features-changed", ident, binary)
                ),
            )
        ),
    )
    return backend, data, events, package


def test_read_features_when_native_info_then_canonical_text_order_and_detached_blocks(
    native_features,
):
    backend, data, events, _ = native_features
    assert backend.get_features() == "".join(
        row["feature"] for row in data["openTypeFeatures"]
    )
    blocks = backend.get_feature_blocks()
    assert [tag for tag, text in blocks["features"]] == ["kern", "liga"]
    blocks["features"].clear()
    assert len(backend.get_feature_blocks()["features"]) == 2 and not events


def test_write_features_when_structured_then_loader_order_history_and_classes_preserved(
    native_features,
):
    backend, data, events, package = native_features
    classes = deepcopy(data["classes"])
    blocks = backend.get_feature_blocks()
    blocks["features"][0] = ("kern", "feature kern { pos A V -20; } kern;\r\n")
    font = RFont(backend)
    font.features.set_blocks(blocks, undo_name="Edit kern feature")
    assert font.features.get_blocks() == blocks
    assert data["classes"] == classes
    assert events == [
        ("init", 0),
        ("Edit kern feature", [package, "features-container"]),
        "clear",
        ("prefix", blocks["prefix"]),
        *blocks["features"],
        ("features-changed", 42, False),
        ("Edit kern feature", [package, "features-container"]),
    ]
    events.clear()
    font.features.set_blocks(blocks)
    font.features.text = font.features.text
    assert not events, "identical structured/text writes must add no history"


@pytest.mark.parametrize(
    "bad",
    [
        {"prefix": "ok", "features": [("kern", "valid"), ("toolong", "bad")]},
        {"prefix": "ok", "features": [("kern", "valid"), ("kern", "duplicate")]},
        {"prefix": "ok", "features": [("kern", "valid"), ("liga", "bad\x00")]},
        {"prefix": "ok", "features": [("kern", "valid"), ("aalt", "reordered")]},
        {"prefix": "\ud800", "features": []},
    ],
)
def test_write_features_when_invalid_batch_then_no_history_or_mutation(
    native_features, bad
):
    backend, data, events, _ = native_features
    before = deepcopy(data)
    with pytest.raises((ValueError, TypeError, UnicodeError)):
        backend.set_feature_blocks(bad)
    assert data == before and not events


def test_write_features_when_arbitrary_text_then_only_split_is_unsupported(
    native_features,
):
    backend, data, events, _ = native_features
    before = deepcopy(data)
    with pytest.raises(UnsupportedCapability, match="set_blocks") as error:
        backend.set_features("# arbitrary replacement\nfeature liga {} liga;\n")
    assert error.value.capability == "font.features.text.split"
    assert data == before and not events


def test_read_features_when_binary_only_then_empty_without_decompilation(
    native_features,
):
    backend, data, events, _ = native_features
    del data["openTypeFeatures"]
    assert backend.get_features() == ""
    assert backend.get_feature_blocks() == {"prefix": "", "features": []}
    assert not events


def test_read_features_when_mcp_unavailable_then_loud_error_without_fragment_fallback(
    native_features, monkeypatch
):
    backend, _, _, _ = native_features
    monkeypatch.setattr(sys.modules["fontpr"], "available", lambda: False)
    with pytest.raises(RuntimeError, match="get_font_info"):
        backend.get_features()


def test_features_when_name_table_would_leave_prefix_on_undo_then_refuse(
    native_features,
):
    backend, data, events, _ = native_features
    before = deepcopy(data)
    blocks = backend.get_feature_blocks()
    blocks["prefix"] += 'table name { nameid 256 "Ω"; } name;\r\n'
    with pytest.raises(ValueError, match=r"Prefix block.*prefix differs"):
        backend.set_feature_blocks(blocks)
    assert data == before and not events


def test_features_when_none_then_refuses_native_language_synthesis_before_history(
    native_features,
):
    backend, data, events, _ = native_features
    before = deepcopy(data)
    with pytest.raises(ValueError, match=r"Prefix block.*#> languagesystem"):
        backend.set_features(None)
    assert data == before and not events


@pytest.mark.parametrize("rows", [[], None])
def test_write_blocks_when_featureless_baseline_then_empty_and_none_are_noops(
    native_features, rows
):
    backend, data, events, _ = native_features
    if rows is None:
        data.pop("openTypeFeatures")
    else:
        data["openTypeFeatures"] = rows
    before = deepcopy(data)
    backend.set_feature_blocks({"prefix": "", "features": []})
    backend.set_features(None)
    assert data == before and not events, "No-op must not allocate storage or history"


def test_write_blocks_when_featureless_baseline_then_explicit_languagesystem_add_succeeds(
    native_features,
):
    backend, data, events, _ = native_features
    data.pop("openTypeFeatures")
    classes = deepcopy(data["classes"])
    blocks = {
        "prefix": "languagesystem DFLT dflt;\n",
        "features": [("kern", "feature kern {} kern;\n")],
    }
    backend.set_feature_blocks(blocks)
    assert backend.get_feature_blocks() == blocks
    assert data["classes"] == classes and events[0] == ("init", 0)


@pytest.mark.parametrize(
    "info",
    [
        None,
        {"openTypeFeatures": None},
        {"openTypeFeatures": [{"feature": "prefix"}, {"feature": "second"}]},
        {"openTypeFeatures": [{"name": "kern", "feature": "code", "unknown": "data"}]},
    ],
)
def test_features_when_unexpected_native_shape_then_refuse_instead_of_losing_data(info):
    from fontlab_fontport.native_features import blocks_from_info

    with pytest.raises((ValueError, TypeError)):
        blocks_from_info(info)


@pytest.mark.parametrize(
    "code, reason",
    [
        ("# introduction\nfeature kern {} kern;\n", "prefix differs"),
        ("feature liga {} liga;\n", "tag differs"),
        ("feature kern {} kern;\nfeature liga {} liga;\n", "code differs"),
        ("unstructured text\n", "prefix differs"),
    ],
)
def test_write_features_when_native_splitter_would_change_block_then_refuse_before_history(
    native_features, code, reason
):
    from fontlab_fontport.native_features import stage_blocks

    backend, data, events, _ = native_features
    before = deepcopy(data)
    blocks = backend.get_feature_blocks()
    blocks["features"][0] = ("kern", code)
    for write in (stage_blocks, backend.set_feature_blocks):
        with pytest.raises(ValueError, match=f"Feature block 'kern'.*{reason}"):
            write(blocks)
    assert data == before and not events, "invalid boundaries must not create history"


def test_write_features_when_prefix_comment_contains_keyword_then_preserve_it(
    native_features,
):
    backend, _, _, _ = native_features
    blocks = backend.get_feature_blocks()
    blocks["prefix"] += "# OpenType Layout feature definitions\n"
    backend.set_feature_blocks(blocks)
    assert backend.get_feature_blocks() == blocks


def test_read_features_when_existing_boundary_is_unstable_then_readable_but_edit_refused(
    native_features,
):
    backend, data, events, _ = native_features
    data["openTypeFeatures"][2]["feature"] = "# introduction\nfeature liga {} liga;\n"
    before = deepcopy(data)
    blocks = backend.get_feature_blocks()
    assert blocks["features"][1][1] == data["openTypeFeatures"][2]["feature"]
    assert backend.get_features() == "".join(
        row["feature"] for row in data["openTypeFeatures"]
    )
    blocks["features"][1] = ("liga", "feature liga {} liga;\n")
    with pytest.raises(
        ValueError, match=r"Current Undo baseline.*Feature block 'liga'"
    ):
        backend.set_feature_blocks(blocks)
    assert data == before and not events


def test_stage_blocks_when_comments_and_body_references_then_preserve_bytes():
    from fontlab_fontport.native_features import split_history_text, stage_blocks

    blocks = {
        "prefix": "# OpenType Layout feature definitions\r\nlanguagesystem DFLT dflt;\r\n",
        "features": [
            (
                "aalt",
                "feature aalt { feature sups; feature liga; } aalt;\r\n# another feature\n",
            )
        ],
    }
    assert stage_blocks(blocks) == blocks
    assert split_history_text(blocks["prefix"] + blocks["features"][0][1]) == blocks


@pytest.mark.parametrize("slot", [{"name": "ccmp"}, {"name": "ccmp", "feature": ""}])
def test_features_when_empty_tagged_slot_then_read_text_noop_and_refuse_lossy_history(
    native_features, slot
):
    backend, data, events, _ = native_features
    data["openTypeFeatures"].append(slot)
    before = deepcopy(data)
    blocks = backend.get_feature_blocks()
    assert [tag for tag, code in blocks["features"]] == ["kern", "liga"]
    assert backend.get_features() == "".join(
        row.get("feature", "") for row in data["openTypeFeatures"]
    )
    backend.set_feature_blocks(blocks)
    assert data == before and not events, (
        "identical text writes must retain empty tagged slots"
    )
    blocks["features"][0] = ("kern", "feature kern {} kern;\n")
    with pytest.raises(
        ValueError, match=r"empty Feature block 'ccmp'.*cannot preserve its tag"
    ):
        backend.set_feature_blocks(blocks)
    assert data == before and not events, "refusal must preserve raw empty rows"


def test_blocks_from_info_when_empty_anonymous_records_then_follow_vfj_loader():
    from fontlab_fontport.native_features import blocks_from_info

    info = {
        "openTypeFeatures": [
            {},
            {"feature": ""},
            {"name": "ccmp"},
            {"feature": "# prefix\n"},
        ]
    }
    assert blocks_from_info(info) == {"prefix": "# prefix\n", "features": []}


@pytest.mark.parametrize("leading", [" ", "\n", "\t\r\n", "# comment\n"])
def test_stage_blocks_when_leading_text_moves_to_prefix_then_refuse(leading):
    from fontlab_fontport.native_features import stage_blocks

    with pytest.raises(
        ValueError, match=r"Feature block 'kern'.*(prefix|code) differs"
    ):
        stage_blocks(
            {"prefix": "", "features": [("kern", leading + "feature kern {} kern;\n")]}
        )


@pytest.mark.parametrize(
    "source, expected",
    [
        ("", {"prefix": "", "features": []}),
        (" \t\n", {"prefix": "", "features": []}),
        (
            "# feature kern {} kern;\r\n",
            {"prefix": "# feature kern {} kern;\r\n", "features": []},
        ),
        (
            "feature aalt { feature sups; } aalt;\n",
            {
                "prefix": "",
                "features": [("aalt", "feature aalt { feature sups; } aalt;\n")],
            },
        ),
        (
            "feature kern {} kern;\n# feature liga {} liga;\n",
            {
                "prefix": "",
                "features": [
                    ("kern", "feature kern {} kern;\n# feature liga {} liga;\n")
                ],
            },
        ),
        (
            "feature kern {} kern;\nfeature liga {} liga;\n",
            {
                "prefix": "",
                "features": [
                    ("kern", "feature kern {} kern;\n"),
                    ("liga", "feature liga {} liga;\n"),
                ],
            },
        ),
    ],
)
def test_split_history_text_when_native_tokens_then_matches_expected(source, expected):
    from fontlab_fontport.native_features import split_history_text

    assert split_history_text(source) == expected


@pytest.mark.parametrize(
    "code",
    [
        "feature kern { lookup kern; feature liga; } kern;\n",
        "feature kern {} kern;\nfeature kern {} kern;\n",
        "feature kern {} kern;",  # Native storage appends LF, getline truncates.
        "feature ",
    ],
)
def test_stage_blocks_when_native_scanner_changes_or_drops_code_then_refuse(code):
    from fontlab_fontport.native_features import stage_blocks

    with pytest.raises(ValueError, match="Feature block 'kern'"):
        stage_blocks({"prefix": "", "features": [("kern", code)]})


def test_split_history_text_when_native_reorders_aalt_and_drops_duplicate_then_match():
    from fontlab_fontport.native_features import split_history_text

    assert split_history_text(
        "feature kern {} kern;\nfeature aalt {} aalt;\nfeature kern {} kern;\n"
    ) == {
        "prefix": "",
        "features": [
            ("aalt", "feature aalt {} aalt;\n"),
            ("kern", "feature kern {} kern;\n"),
        ],
    }


def test_split_history_text_when_single_line_name_table_then_keeps_unread_byte():
    from fontlab_fontport.native_feature_split import _without_name_table
    from fontlab_fontport.native_features import split_history_text

    source = "table name { } name;{"
    assert _without_name_table(source.encode()) == b"{"
    assert split_history_text(source) == {"prefix": "{\n", "features": []}


@pytest.mark.parametrize("code", ["feature\n", "feature kern {} kern;\nfeature\n"])
def test_stage_blocks_when_tagless_trailing_keyword_then_refuse_before_native(code):
    from fontlab_fontport.native_features import stage_blocks

    with pytest.raises(ValueError, match=r"Feature block 'kern'.*no tag"):
        stage_blocks(
            {"prefix": "languagesystem DFLT dflt;\n", "features": [("kern", code)]}
        )


@pytest.mark.parametrize(
    "prefix",
    [
        "",
        "# preface\n",
        "languagesystem\tDFLT dflt;\n",
        "@class = [A];\n",
        "# c\r\n \r\ninclude(x.fea);\r\n",
        "\r\ninclude(x.fea);\r\n",
    ],
)
def test_write_blocks_when_changing_prefix_needs_synthesis_then_refuse_before_history(
    native_features, prefix
):
    from fontlab_fontport.native_features import stage_blocks

    backend, data, events, _ = native_features
    before = deepcopy(data)
    blocks = backend.get_feature_blocks()
    blocks["prefix"] = prefix
    assert stage_blocks(blocks) == blocks, (
        "Pure split-back staging must not check allocation"
    )
    with pytest.raises(
        ValueError, match=r"Prefix block.*#> languagesystem.*glyph scripts"
    ):
        backend.set_feature_blocks(blocks)
    assert data == before and not events


@pytest.mark.parametrize(
    "prefix",
    [
        "languagesystem DFLT dflt;\n",
        "# languagesystem literal in a comment suppresses native synthesis\n",
        "include(external.fea);\n",
        "# comment\n \ninclude(external.fea);\n",
        "# comment\r \rinclude(external.fea);\n",
        "include(external.fea);\r\n",
    ],
)
def test_write_blocks_when_native_synthesis_is_suppressed_then_keep_exact_bytes(
    native_features, prefix
):
    from fontlab_fontport.native_features import stage_blocks

    blocks = {"prefix": prefix, "features": [("kern", "feature kern {} kern;\n")]}
    assert stage_blocks(blocks) == blocks
    backend, _, _, _ = native_features
    backend.set_feature_blocks(blocks)
    assert backend.get_feature_blocks() == blocks
