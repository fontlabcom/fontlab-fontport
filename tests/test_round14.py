# this_file: tests/test_round14.py
"""C4 geometry history and boundary regressions, without a native host."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from fontlab_fontport.errors import UnsupportedCapability
from fontlab_fontport.host import NativeFontBackend


def test_geometry_uses_private_working_shapes_after_history_snapshot():
    class Shape:
        def __init__(self, points):
            self.points = points
        def clone(self):
            return deepcopy(self)
    saved = Shape([(0, 0), (100, 0)])
    layer = SimpleNamespace(shapes=[saved])
    layer.removeShape = lambda shape: layer.shapes.remove(shape)
    layer.insertShape = lambda index, shape: layer.shapes.insert(index, shape)
    NativeFontBackend._own_shapes(layer)
    layer.shapes[0].points.clear()
    assert saved.points == [(0, 0), (100, 0)], 'Undo snapshot must retain original geometry'
    assert layer.shapes[0] is not saved


def test_native_multi_membership_is_named_before_write():
    from fontlab_fontport.native_groups import write_groups
    with pytest.raises(UnsupportedCapability) as error:
        write_groups(None, {'public.kern1.a': ('A',), 'public.kern1.b': ('A',)}, 'Owned test')
    assert error.value.capability == 'groups.multiMembership'


def test_structured_capability_exposes_key_master_scope():
    from fontlab_fontport.capabilities import NATIVE_CAPABILITIES, STRUCTURED_ROUTES
    for field in ('openTypeOS2Panose','openTypeOS2WeightClass','openTypeOS2WidthClass','postscriptStemSnapH','postscriptStemSnapV'):
        assert STRUCTURED_ROUTES[field]['bound'] == 'key-master'
        assert NATIVE_CAPABILITIES['info.'+field]['bound'] == 'key-master'
    assert not NATIVE_CAPABILITIES['glyph.exactSingleUndo']['supported']


def test_undo_receipt_checks_immutable_mcp_contours(monkeypatch):
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers"))
    from round10_payloads import geometry_receipt, geometry_snapshot
    before = {'layers':[{'name':'Regular','elements':[{'elementData':{'contours':[{'nodes':['0 0 l','100 0 l','0 100 l']} ]}}]}]}
    expected = geometry_snapshot(before)
    before['layers'][0]['elements'][0]['elementData']['contours'][0]['nodes'][0] = '50 50 l'
    receipt = geometry_receipt(before, expected)
    assert receipt['geometry_equal'] is False
    assert receipt['observed_geometry'] != receipt['expected_geometry']


def test_geometry_false_overrides_equal_and_is_saved(driver, tmp_path):
    reply = {'equal': True, 'geometry_equal': False, 'observed_geometry': 'edited', 'expected_geometry': 'baseline'}
    client = SimpleNamespace(run=lambda *a, **kw: SimpleNamespace(value=reply))
    run = driver.Run(client, tmp_path, [])
    run.step('glyph-contours-undo-read', '')
    assert run.failures[0]['result'] == reply
    assert 'edited' in run.receipts.read_text()


@pytest.fixture
def driver(monkeypatch):
    import importlib
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers"))
    return importlib.import_module('round10')


def test_geometry_probe_checks_point_edits_and_extra_checkpoint(driver):
    phases = dict(driver.glyph_phases())
    assert 'glyph-live-pen-edit' in phases and 'glyph-appendPoint-edit' in phases
    assert 'geometry_changed_when_required=not True' in phases['glyph-contours-read']
    assert 'before_geometry' in phases['glyph-contours-undo-read']
    assert 'actionUndo' in phases['glyph-contours-undo-checkpoint']
    assert 'geometry_receipt' in phases['glyph-contours-undo-checkpoint-read']


def test_values_close_when_float32_readback_then_equal_within_atol(monkeypatch):
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers"))
    from round10_payloads import (
        READBACK_ATOL,
        geometry_receipt,
        geometry_snapshot,
        payload_equal,
        values_close,
    )
    assert READBACK_ATOL == 1e-3
    assert values_close(10.4, 10.3999996) and values_close(10, 10.0004)
    assert not values_close(10.4, 10.402) and not values_close(1, 1.0011)
    assert values_close('10.4 5 l', '10.3999996 5.0004 l')
    assert not values_close('10.4 5 l', '10.4 5 o') and not values_close('1 l', '1 2 l')
    assert values_close({'a': [1, 'x 2']}, {'a': [1.0004, 'x 2.0004']})
    assert not values_close({'a': 1}, {'b': 1}) and not values_close([1], [1, 2])
    assert not values_close(True, 1) and values_close(None, None) and not values_close('a', 1)
    def node(n):
        return {'layers': [{'name': 'R', 'elements': [{'elementData': {'contours': [{'nodes': [n]}]}}]}]}
    assert payload_equal(node('10.4 0 l'), node('10.3999996 0 l'))
    assert not payload_equal(node('10.4 0 l'), node('10.5 0 l'))
    receipt = geometry_receipt(node('10.3999996 0 l'), geometry_snapshot(node('10.4 0 l')))
    assert receipt['geometry_equal'] is True
    assert geometry_receipt(node('11 0 l'), geometry_snapshot(node('10.4 0 l')))['geometry_equal'] is False
