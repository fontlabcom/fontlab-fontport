# this_file: tests/test_ufo_feature_source.py
"""Literal source oracles for the private UFO candidate; no backend writes."""
from importlib import import_module

import pytest

from fontlab_fontport import ufo_features as helper


@pytest.mark.parametrize('source,prefix,rows', [
    ('', '', []),
    (' \t\r\n\u00a0é', ' \t\r\n\u00a0é', []),
    ('# é\rfeature liga {\rsub f i by fi;\r} liga;', '# é\r', [('liga', 'feature liga {\rsub f i by fi;\r} liga;')]),
    ('feature liga {\n} liga;\n', '', [('liga', 'feature liga {\n} liga;\n')]),
    ('feature liga {\r\n} liga;\r\n', '', [('liga', 'feature liga {\r\n} liga;\r\n')]),
    ('feature liga {\r\n} liga;\rfeature kern {\n} kern;', '', [('liga', 'feature liga {\r\n} liga;\r'), ('kern', 'feature kern {\n} kern;')]),
    ('  feature liga {} liga; feature kern {} kern;', '  ', [('liga', 'feature liga {} liga; '), ('kern', 'feature kern {} kern;')]),
    ('feature liga {} liga;\n # keep\n  feature kern {} kern;', '', [('liga', 'feature liga {} liga;\n # keep\n  '), ('kern', 'feature kern {} kern;')]),
    ('# feature fake {\rfeature liga # header\n { ???\u00a0sub ;', '# feature fake {\r', [('liga', 'feature liga # header\n { ???\u00a0sub ;')]),
    ('table name { nameid 1 "feature fake {\n é }"; } name;\nfeature liga { lookup L { sub a by b; } L; feature kern; } liga;', 'table name { nameid 1 "feature fake {\n é }"; } name;\n', [('liga', 'feature liga { lookup L { sub a by b; } L; feature kern; } liga;')]),
    ('include # comment\r (never/#"feature fake {);\nfeature liga {} liga;', 'include # comment\r (never/#"feature fake {);\n', [('liga', 'feature liga {} liga;')]),
    ('@feature = [a]; \\feature featureName includeOther; feature liga;\nfeature kern {} kern;', '@feature = [a]; \\feature featureName includeOther; feature liga;\n', [('kern', 'feature kern {} kern;')]),
    ('feature liga {} liga;feature aalt {} aalt;feature liga {} liga;', '', [('liga', 'feature liga {} liga;'), ('aalt', 'feature aalt {} aalt;'), ('liga', 'feature liga {} liga;')]),
    ('feature\u00a0liga\u00a0{', '', [('liga', 'feature\u00a0liga\u00a0{')]),
    ('feature liga { nameid 1 "slash\\"; } liga;', '', [('liga', 'feature liga { nameid 1 "slash\\"; } liga;')]),
])
def test_read_when_supported_then_literal_raw_slices(source, prefix, rows):
    expected = {'prefix': prefix, 'features': rows}
    assert helper.read_blocks(source) == expected
    assert helper.stage_blocks(source, expected) is None
    assert helper.stage_blocks('', expected) == (source if source else None)
    assert prefix + ''.join(code for _, code in rows) == source


OPAQUE = [
    '"unterminated', 'include(missing', 'anon TEST { arbitrary } TEST;',
    'anonymous TEST { arbitrary } TEST;', '}', 'table name {',
    'feature liga { feature kern {} kern; } liga;',
    'feature abc {} abc;', 'feature abcde {} abcde;', 'feature éééé {} éééé;',
    'feature liga {} liga; feature abc {} abc; feature kern {} kern;',
    'feature', 'feature liga', 'feature {', 'feature liga ???',
]


@pytest.mark.parametrize('source', OPAQUE)
def test_read_when_opaque_then_full_prefix_and_exact_noop(source):
    expected = {'prefix': source, 'features': []}
    assert helper.read_blocks(source) == expected
    assert helper.stage_blocks(source, expected) is None
    with pytest.raises(ValueError, match='unsupported'):
        helper.stage_blocks(source, {'prefix': source + ' ', 'features': []})


@pytest.mark.parametrize('source', OPAQUE)
def test_stage_when_requested_opaque_then_refuse(source):
    with pytest.raises(ValueError, match='unsupported'):
        helper.stage_blocks('', {'prefix': source, 'features': []})


def test_stage_when_cr_sibling_edit_then_literal_entire_source():
    current = '# header\nfeature liga {\nsub f i by fi;\n} liga;\nfeature kern {\rpos A V -80;\r} kern;'
    requested = {'prefix': '# header\n', 'features': [
        ('liga', 'feature liga {\nsub f l by fl;\n} liga;\n'),
        ('kern', 'feature kern {\rpos A V -80;\r} kern;'),
    ]}
    assert helper.stage_blocks(current, requested) == '# header\nfeature liga {\nsub f l by fl;\n} liga;\nfeature kern {\rpos A V -80;\r} kern;'


@pytest.mark.parametrize('rows,expected', [
    ([('liga', 'feature liga {???} liga;'), ('liga', 'feature liga {} liga;')], 'feature liga {???} liga;feature liga {} liga;'),
    ([('liga', 'feature liga {} liga;')], 'feature liga {} liga;'),
    ([('liga', 'feature liga {} liga;'), ('aalt', 'feature aalt {} aalt;')], 'feature liga {} liga;feature aalt {} aalt;'),
    ([], ''),
])
def test_stage_when_duplicate_rows_changed_then_preserve_requested_order(rows, expected):
    current = 'feature aalt {} aalt;feature liga {} liga;feature liga {} liga;'
    assert helper.stage_blocks(current, {'prefix': '', 'features': rows}) == expected


@pytest.mark.parametrize('requested', [
    {'prefix': 'feature liga {} liga;', 'features': []},
    {'prefix': '', 'features': [('kern', 'feature liga {} liga;')]},
    {'prefix': '', 'features': [('liga', 'feature liga {} liga;'), ('kern', ' feature kern {} kern;')]},
    {'prefix': '', 'features': [('liga', 'feature liga {} liga;feature kern {} kern;')]},
])
def test_stage_when_partition_mismatch_then_refuse_even_equal_concatenation(requested):
    with pytest.raises(ValueError, match='partition'):
        helper.stage_blocks('feature liga {} liga;', requested)


@pytest.mark.parametrize('requested,error', [
    (None, TypeError), ([], TypeError), ({}, ValueError),
    ({'prefix': '', 'features': [], 'extra': 1}, ValueError),
    ({'prefix': '', 'features': iter([])}, TypeError),
    ({'prefix': '', 'features': ['xx']}, TypeError),
    ({'prefix': '', 'features': [('liga',)]}, ValueError),
    ({'prefix': '', 'features': [(1, '')]}, TypeError),
    ({'prefix': '', 'features': [('abc', '')]}, ValueError),
    ({'prefix': '', 'features': [('éééé', '')]}, ValueError),
    ({'prefix': '', 'features': [('a b ', '')]}, ValueError),
    ({'prefix': '', 'features': [('liga', 1)]}, TypeError),
    ({'prefix': 1, 'features': []}, TypeError),
    ({'prefix': '\x00', 'features': []}, ValueError),
    ({'prefix': '\ud800', 'features': []}, ValueError),
    ({'prefix': '', 'features': [('liga', '\x00')]}, ValueError),
    ({'prefix': '', 'features': [('liga', '\ud800')]}, ValueError),
    ({'prefix': '', 'features': [('\x00abc', '')]}, ValueError),
    ({'prefix': '', 'features': [('\ud800abc', '')]}, ValueError),
])
def test_stage_when_invalid_shape_or_text_then_refuse(requested, error):
    with pytest.raises(error):
        helper.stage_blocks('', requested)


@pytest.mark.parametrize('source,error', [(None, TypeError), ('\x00', ValueError), ('\ud800', ValueError)])
def test_read_when_invalid_text_then_refuse(source, error):
    with pytest.raises(error):
        helper.read_blocks(source)


def test_read_and_stage_when_mutable_containers_then_detached():
    source = 'feature liga {} liga;'
    first = helper.read_blocks(source)
    first['features'].clear()
    first['prefix'] = 'changed'
    assert helper.read_blocks(source) == {'prefix': '', 'features': [('liga', source)]}
    requested = {'prefix': '', 'features': [['liga', source]]}
    assert helper.stage_blocks('', requested) == source
    assert requested == {'prefix': '', 'features': [['liga', source]]}
    assert helper.stage_blocks(source, {'prefix': '', 'features': (('liga', source),)}) is None


@pytest.mark.parametrize('source,prefix,rows', [
    ('markClass feature <anchor 0 0> @MC;\nfeature liga { sub A B by A; } liga;\n', 'markClass feature <anchor 0 0> @MC;\n', [('liga', 'feature liga { sub A B by A; } liga;\n')]),
    ('@C = [feature liga];\nfeature kern { pos A B -25; } kern;\n', '@C = [feature liga];\n', [('kern', 'feature kern { pos A B -25; } kern;\n')]),
    ('@C = [ feature liga ];\nfeature kern {} kern;', '@C = [ feature liga ];\n', [('kern', 'feature kern {} kern;')]),
])
def test_read_when_feature_is_prefix_glyph_then_only_declaration_splits(source, prefix, rows):
    assert helper.read_blocks(source) == {'prefix': prefix, 'features': rows}


def test_read_when_anonymous_keyword_is_glyph_then_prefix_preserved():
    source = 'markClass anonymous <anchor 0 0> @MC;\nmarkClass anon <anchor 0 0> @MC;\nfeature liga {} liga;'
    assert helper.read_blocks(source) == {
        'prefix': 'markClass anonymous <anchor 0 0> @MC;\nmarkClass anon <anchor 0 0> @MC;\n',
        'features': [('liga', 'feature liga {} liga;')],
    }


@pytest.mark.parametrize('source', ['feature @abc {} @abc;', 'feature \\abc {} \\abc;'])
def test_read_when_header_tag_is_not_bare_then_opaque(source):
    assert helper.read_blocks(source) == {'prefix': source, 'features': []}
    assert helper.stage_blocks(source, {'prefix': source, 'features': []}) is None


# Complete owned UFO fixtures; no Qt or host imports.
base64 = import_module("base64")
json = import_module("json")
Mapping = import_module("collections.abc").Mapping
deepcopy = import_module("copy").deepcopy
SimpleNamespace = import_module("types").SimpleNamespace

attrs = import_module("attrs")
Font = import_module("ufoLib2").Font
Anchor = import_module("ufoLib2.objects").Anchor
Guideline = import_module("ufoLib2.objects").Guideline
Image = import_module("ufoLib2.objects").Image
Component = import_module("ufoLib2.objects").Component

def freeze(value):
        if attrs.has(type(value)):
            return {"type": type(value).__module__ + "." + type(value).__qualname__,
                    "fields": {f.name: freeze(getattr(value, f.name)) for f in attrs.fields(type(value))}}
        if isinstance(value, Mapping):
            return {"mapping": [[freeze(k), freeze(v)] for k, v in sorted(value.items(), key=lambda kv: repr(kv[0]))]}
        if isinstance(value, (set, frozenset)):
            items = [freeze(x) for x in value]
            return {"type": type(value).__name__, "items": sorted(items, key=lambda x: json.dumps(x, sort_keys=True))}
        if isinstance(value, (list, tuple)):
            return {"type": type(value).__name__, "items": [freeze(x) for x in value]}
        if isinstance(value, bytes):
            return {"bytes": value.hex()}
        if value is None or type(value) in (str, int, bool):
            return value
        if isinstance(value, float):
            return {"float": value.hex()}
        raise TypeError("Unqualified fixture snapshot type: " + str(type(value)))

def font_fixture(text, marker):
        font = Font()
        font.info.familyName = "Owned same label"
        font.info.styleName = "Regular"
        font.info.unitsPerEm = 1000
        font.info.ascender = 800
        font.info.descender = -200
        font.features.text = text
        font.lib["owned"] = {"marker": marker, "nested": [True, 1, 1.5, b"\x00\xff"]}
        font.groups["public.kern1.A"] = ["A"]
        font.kerning[("A", "B")] = -25.5
        font.images["owned.png"] = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg==")
        font.data["owned/payload.bin"] = b"owned\0\xff"
        g = font.newGlyph("A")
        g.width = 600.25
        g.height = 900.5
        g.unicodes = [65]
        g.note = "unchanged Ω"
        g.lib["owned"] = [marker]
        g.anchors = [Anchor(100.5, 700, "top")]
        g.guidelines = [Guideline(25, 0, 90, "guide")]
        g.image = Image("owned.png", (1, 0, 0, 1, 13.5, -17.75))
        pen = g.getPen()
        pen.moveTo((0,0))
        pen.lineTo((100,0))
        pen.lineTo((100,100))
        pen.closePath()
        g.components.append(Component("B", (1, 0, 0, 1, 10.5, 20)))
        font.newGlyph("B").width = 420
        layer = font.layers.newLayer("owned.background")
        layer.lib["owned"] = marker
        layer.newGlyph("untouched").width = 333
        return font

@pytest.fixture
def real_backend(monkeypatch):
    from fontlab_fontport.fontdata import RFeatures
    from fontlab_fontport.live import RFont
    from fontlab_fontport.memory import UFOBackend
    models = [font_fixture('', marker) for marker in ('A', 'B')]
    backends = [UFOBackend(model) for model in models]
    fonts = [RFont(backend) for backend in backends]
    expected = deepcopy(models)
    logical, writes = [], []
    original = RFeatures.set_blocks
    def request(self, values, **kwargs):
        logical.append((self, deepcopy(values)))
        return original(self, values, **kwargs)
    monkeypatch.setattr(RFeatures, 'set_blocks', request)
    for backend in backends:
        setter = backend.set_features
        def write(text, *, _backend=backend, _setter=setter, **kwargs):
            writes.append((_backend, text, kwargs))
            return _setter(text, **kwargs)
        monkeypatch.setattr(backend, 'set_features', write)
    state = SimpleNamespace(models=models, expected=expected, backends=backends,
                            fonts=fonts, logical=logical, writes=writes)
    yield state
    assert [freeze(model) for model in models] == [freeze(model) for model in expected]
    assert all(not backend.closed and backend.saved_path is None for backend in backends)


@pytest.mark.parametrize('source,blocks', [
    ('# prefix\nfeature liga {\n???\u00a0é\n} liga;\nfeature kern {\rpos A B -25;\r} kern;',
     {'prefix': '# prefix\n', 'features': [('liga', 'feature liga {\n???\u00a0é\n} liga;\n'), ('kern', 'feature kern {\rpos A B -25;\r} kern;')]}),
    ('feature liga {\r\n???\r\n} liga;', {'prefix': '', 'features': [('liga', 'feature liga {\r\n???\r\n} liga;')]}),
    ('feature liga { sub ;', {'prefix': '', 'features': [('liga', 'feature liga { sub ;')]}),
    ('include(never/open/this.fea);\nfeature anon {} anon;', {'prefix': 'include(never/open/this.fea);\n', 'features': [('anon', 'feature anon {} anon;')]}),
    ('feature liga {} liga;feature aalt {} aalt;feature liga {???} liga;', {'prefix': '', 'features': [('liga', 'feature liga {} liga;'), ('aalt', 'feature aalt {} aalt;'), ('liga', 'feature liga {???} liga;')]}),
    (' \t\r\né', {'prefix': ' \t\r\né', 'features': []}),
])
def test_real_backend_when_changed_then_exact_readback_and_one_raw_write(real_backend, source, blocks):
    state = real_backend
    features = state.fonts[0].features
    features.set_blocks(blocks, undo_name='owned exact source')
    state.expected[0].features.text = source
    assert state.models[0].features.text == source
    assert features.get_blocks() == blocks
    assert len(state.logical) == len(state.writes) == 1
    features.set_blocks(blocks)
    assert len(state.logical) == 2 and len(state.writes) == 1
    returned = features.get_blocks()
    returned['features'].clear()
    returned['prefix'] = 'detached'
    assert features.get_blocks() == blocks


@pytest.mark.parametrize('source', [*OPAQUE,
    'feature liga {} liga\nanon TEST { raw } TEST;',
    'feature liga {} liga anonymous TEST { raw } TEST;',
])
def test_real_backend_when_opaque_then_exact_noop_and_zero_write_refusal(real_backend, source):
    state = real_backend
    state.models[0].features.text = state.expected[0].features.text = source
    features = state.fonts[0].features
    assert features.get_blocks() == {'prefix': source, 'features': []}
    features.set_blocks({'prefix': source, 'features': []})
    assert not state.writes
    with pytest.raises(ValueError, match='unsupported'):
        features.set_blocks({'prefix': source + ' ', 'features': []})
    assert len(state.logical) == 2 and not state.writes


@pytest.mark.parametrize('rows,expected', [
    ([('liga', 'feature liga {???} liga;'), ('liga', 'feature liga {} liga;')], 'feature liga {???} liga;feature liga {} liga;'),
    ([('liga', 'feature liga {} liga;')], 'feature liga {} liga;'),
    ([('liga', 'feature liga {} liga;'), ('aalt', 'feature aalt {} aalt;')], 'feature liga {} liga;feature aalt {} aalt;'),
    ([], ''),
])
def test_real_backend_when_duplicate_rows_replaced_or_cleared_then_exact(real_backend, rows, expected):
    state = real_backend
    state.models[0].features.text = state.expected[0].features.text = 'feature aalt {} aalt;feature liga {} liga;feature liga {} liga;'
    state.fonts[0].features.set_blocks({'prefix': '', 'features': rows})
    state.expected[0].features.text = expected
    assert state.models[0].features.text == expected
    assert len(state.logical) == len(state.writes) == 1
    state.fonts[0].features.set_blocks({'prefix': '', 'features': rows})
    assert len(state.writes) == 1


def test_real_backend_when_equal_concatenation_wrong_partition_then_no_raw_write(real_backend):
    state = real_backend
    state.models[0].features.text = state.expected[0].features.text = 'feature liga {} liga;'
    with pytest.raises(ValueError, match='partition'):
        state.fonts[0].features.set_blocks({'prefix': 'feature liga {} liga;', 'features': []})
    assert len(state.logical) == 1 and not state.writes


def test_real_backend_when_saved_then_exact_feature_file_bytes(real_backend, tmp_path):
    state = real_backend
    source = '# é\nfeature liga {\r???\r} liga;'
    state.fonts[0].features.set_blocks({'prefix': '# é\n', 'features': [('liga', 'feature liga {\r???\r} liga;')]})
    state.expected[0].features.text = source
    # Save an owned detached copy: this checks the file bytes, not newline-normalizing reopen.
    copied = deepcopy(state.models[0])
    path = tmp_path / 'owned.ufo'
    copied.save(path)
    assert (path / 'features.fea').read_bytes() == b'# \xc3\xa9\nfeature liga {\r???\r} liga;'


def test_read_when_named_feature_is_anon_then_exact_named_partition():
    assert helper.read_blocks('feature anon {} anon;') == {
        'prefix': '', 'features': [('anon', 'feature anon {} anon;')],
    }


def test_stage_when_named_anon_is_unchanged_then_noop():
    assert helper.stage_blocks('feature anon {} anon;', {
        'prefix': '', 'features': [('anon', 'feature anon {} anon;')],
    }) is None


def test_stage_when_named_anon_is_new_then_exact_source():
    assert helper.stage_blocks('', {
        'prefix': '', 'features': [('anon', 'feature anon {} anon;')],
    }) == 'feature anon {} anon;'


def test_stage_when_named_anon_changes_then_exact_source():
    assert helper.stage_blocks('feature anon {} anon;', {
        'prefix': '', 'features': [('anon', 'feature anon { sub a by b; } anon;')],
    }) == 'feature anon { sub a by b; } anon;'


@pytest.mark.parametrize('source,prefix,changed_prefix,expected', [
    ('lookup anon { sub a by b; } anon; feature liga {} liga;',
     'lookup anon { sub a by b; } anon; ',
     'lookup anon { sub a by c; } anon; ',
     'lookup anon { sub a by c; } anon; feature liga {} liga;'),
    ('lookup anonymous { sub a by b; } anonymous; feature liga {} liga;',
     'lookup anonymous { sub a by b; } anonymous; ',
     'lookup anonymous { sub a by c; } anonymous; ',
     'lookup anonymous { sub a by c; } anonymous; feature liga {} liga;'),
])
def test_read_and_stage_when_lookup_name_is_anonymous_keyword_then_prefix(source, prefix, changed_prefix, expected):
    assert helper.read_blocks(source) == {
        'prefix': prefix, 'features': [('liga', 'feature liga {} liga;')],
    }
    assert helper.stage_blocks(source, {
        'prefix': prefix, 'features': [('liga', 'feature liga {} liga;')],
    }) is None
    assert helper.stage_blocks(source, {
        'prefix': changed_prefix, 'features': [('liga', 'feature liga {} liga;')],
    }) == expected


ANONYMOUS_AFTER_FEATURE = [
    'feature liga {} liga\nanon TEST { raw } TEST;',
    'feature liga {} liga anon TEST { raw } TEST;',
    'feature liga {} liga\nanonymous TEST { raw } TEST;',
    'feature liga {} liga anonymous TEST { raw } TEST;',
    'feature liga {} liga\ranon # opener\r TEST # raw\n { raw } TEST;',
]


@pytest.mark.parametrize('source', ANONYMOUS_AFTER_FEATURE)
def test_read_when_anonymous_follows_semicolon_free_feature_then_opaque(source):
    assert helper.read_blocks(source) == {'prefix': source, 'features': []}


@pytest.mark.parametrize('source', ANONYMOUS_AFTER_FEATURE)
def test_stage_when_opaque_anonymous_is_unchanged_then_noop(source):
    assert helper.stage_blocks(source, {'prefix': source, 'features': []}) is None


@pytest.mark.parametrize('source', ANONYMOUS_AFTER_FEATURE)
def test_stage_when_anonymous_changes_then_refuse(source):
    with pytest.raises(ValueError, match='unsupported'):
        helper.stage_blocks(source, {'prefix': source + ' ', 'features': []})


@pytest.mark.parametrize('source', ANONYMOUS_AFTER_FEATURE)
def test_stage_when_anonymous_is_hidden_in_named_slice_then_refuse(source):
    with pytest.raises(ValueError, match='unsupported'):
        helper.stage_blocks(source, {'prefix': '', 'features': [('liga', source + ' ')]})


@pytest.mark.parametrize('source', ANONYMOUS_AFTER_FEATURE)
def test_stage_when_proposed_anonymous_follows_feature_then_refuse(source):
    with pytest.raises(ValueError, match='unsupported'):
        helper.stage_blocks('', {'prefix': '', 'features': [('liga', source)]})


@pytest.mark.parametrize('values,error', [
    (None, TypeError), ({}, ValueError),
    ({'prefix': '', 'features': 'bad'}, TypeError),
    ({'prefix': '', 'features': [('liga',)]}, ValueError),
    ({'prefix': 1, 'features': []}, TypeError),
    ({'prefix': '\x00', 'features': []}, ValueError),
    ({'prefix': '\ud800', 'features': []}, ValueError),
    ({'prefix': '', 'features': [('abc', '')]}, ValueError),
    ({'prefix': '', 'features': [('liga', 1)]}, TypeError),
    ({'prefix': '', 'features': [('kern', 'feature liga {} liga;')]}, ValueError),
])
def test_real_backend_when_invalid_request_then_no_raw_write(real_backend, values, error):
    with pytest.raises(error):
        real_backend.fonts[0].features.set_blocks(values)
    assert not real_backend.writes


@pytest.mark.parametrize('source', [
    'feature abc { } abc;', 'feature abcde { } abcde;', 'feature Ωabc { } Ωabc;',
    'feature liga {} liga;feature Ωabc { } Ωabc;feature kern {} kern;',
])
def test_real_backend_when_raw_tag_unsupported_then_opaque_noop_and_explicit_raw_replacement(real_backend, source):
    state = real_backend
    state.models[0].features.text = state.expected[0].features.text = source
    features = state.fonts[0].features
    assert features.get_blocks() == {'prefix': source, 'features': []}
    features.set_blocks({'prefix': source, 'features': []})
    with pytest.raises(ValueError, match='unsupported'):
        features.set_blocks({'prefix': source + ' ', 'features': []})
    assert not state.writes
    features.text = '# deliberately replaced\n'
    state.expected[0].features.text = '# deliberately replaced\n'
    assert features.text == '# deliberately replaced\n' and len(state.writes) == 1
