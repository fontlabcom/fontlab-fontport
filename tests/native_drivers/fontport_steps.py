# this_file: tests/native_drivers/fontport_steps.py
"""Small native calls composed by the host driver; no FontLab imports here."""

from batch_driver import batch_phases
from feature_steps import feature_phases
from info_steps import info_phases


def phases(*, features_only=False):
    # The purge still names fontlab_glyport. It came with the B10 Vanilla driver
    # (efcac8f), when Fontport's Vanilla imported Glyport; no Fontport phase
    # imports Glyport now (issue 122 T12). FontLab keeps modules across Remopy
    # calls, so a Glyport that an earlier run loaded in the same session stays
    # live unless purged, and driver_args.py still resolves a Glyport origin for
    # the receipt. Remove both together when the driver stops asking for it.
    yield (
        "purge-stale-project-modules",
        "import sys\nfor name in list(sys.modules):\n    if any(name == root or name.startswith(root + '.') for root in ('fontlab_fontport', 'fontlab_glyport')):\n        del sys.modules[name]",
    )
    for name in (
        "defcon",
        "fontParts.world",
        "ufoLib2",
        "fontPens.flattenPen",
        "fontTools.designspaceLib",
        "fontlab_fontport.world",
        "fontlab_fontport.designspace",
        "fontlab_fontport.export",
        "fontlab_fontport.operations",
        "fontlab_fontport.native_features",
    ):
        code = f"import {name}"
        root = name.split(".")[0]
        if root in ("fontlab_fontport", "fontlab_glyport"):
            code += f"\nfrom pathlib import Path\nassert str(Path({root}.__file__).resolve()) == origins[{root!r}], {root}.__file__"
        yield "warm-" + name, code
    yield (
        "setup",
        """
from pathlib import Path
from copy import deepcopy
from fontlab_fontport.world import FontWorld, register
from fontlab_fontport.designspace import Designspace
from fontlab_fontport.export import export_ufo_subset
from fontTools.pens.recordingPen import RecordingPen
from fontPens.flattenPen import FlattenPen
from PythonQt import QtGui
import fontlab
environment = FontWorld()
def different_info_value(value):
    if isinstance(value, str):
        return value + ' alternate'
    if isinstance(value, int):
        return value + 1
    value = deepcopy(value)
    if isinstance(value[0], dict):
        value[0]['string'] += ' alternate'
    else:
        value[0] += 1
    return value
def action(name):
    control = fontlab.MainWindow().findChild(QtGui.QAction, name)
    if control is None or not control.enabled:
        raise RuntimeError("Unavailable native action: " + name)
    control.trigger()
""",
    )
    yield (
        "open-medi",
        "font = environment.OpenFont(paths['medi'])\nbackend = font._backend",
    )
    if features_only:
        yield from feature_phases()
        yield "feature-close-medi", "font.close()"
        yield (
            "feature-open-plum",
            "font = environment.OpenFont(paths['plum'])\nbackend = font._backend",
        )
        yield (
            "feature-plum-metadata-timing",
            "info = read_info(backend.font_id)\nresult = {'metadata_bytes': len(json.dumps(info)), 'stored_feature_records': len(info.get('openTypeFeatures', []))}",
        )
        yield "feature-close-plum", "font.close()"
        return
    yield (
        "world",
        """
from fontParts import world
with register(environment):
    assert world.CurrentFont() is font and world.AllFonts()[0] is font
    assert world.RFont(font) is font
result = {"module": __import__('fontlab_fontport.world', fromlist=['world']).__file__}
""",
    )
    yield (
        "pens",
        """
recording = RecordingPen()
font['A'].draw(FlattenPen(recording, approximateSegmentLength=20, segmentLines=True))
assert recording.value
result = len(recording.value)
""",
    )
    yield from info_phases()
    yield (
        "lib-comparison-setup",
        """
from fontlab_fontport.fontdata import same_lib
def compare_lib(expected, observed):
    keys = set(expected) | set(observed)
    mismatches = sorted(key for key in keys
        if key not in expected or key not in observed or not same_lib(expected[key], observed[key]))
    return {'exact': not mismatches, 'mismatches': mismatches,
            'expected_repr': {key: repr(expected[key]) if key in expected else '<missing>' for key in keys},
            'observed_repr': {key: repr(observed[key]) if key in observed else '<missing>' for key in keys}}
""",
    )
    yield (
        "lib-foreign-probes",
        """
p = backend._package()
foreign = {'fontport.probe.cr': 'x\\r\\ny\\rz', 'fontport.probe.null': None,
           'fontport.probe.big': 2**53 + 1, 'fontport.probe.nested': {'null': None, 'valid': 1}}
p.packageLib = {**dict(p.packageLib), **foreign}
observed = backend.get_lib()
probe_mismatches = [key for key, value in foreign.items()
                    if key not in observed or type(observed[key]) is not type(value) or observed[key] != value]
result = {'exact': not probe_mismatches, 'mismatches': probe_mismatches,
          'expected_repr': {key: repr(value) for key, value in foreign.items()},
          'observed_repr': {key: repr(observed.get(key)) for key in foreign}}
""",
    )
    yield "lib-baseline", "lib_before = deepcopy(backend.get_lib())"
    yield (
        "lib-apply",
        """
payload = {'text': 'Unicode Ω & <>\\r\\nexact\\r', 'values': [0, True, 2.5]}
font.lib['org.fontlab.fontport.acceptance'] = payload
assert backend.get_lib() == {**lib_before, 'org.fontlab.fontport.acceptance': payload}
""",
    )
    yield "lib-undo", "action('actionUndo')"
    yield "lib-undo-readback", "assert backend.get_lib() == lib_before"
    yield "lib-redo", "action('actionRedo')"
    yield (
        "lib-redo-readback",
        "assert font.lib['org.fontlab.fontport.acceptance'] == payload",
    )
    yield (
        "lib-identical-noop",
        """
p = backend._package()
before_history = p.currentHistoryState()
font.lib['org.fontlab.fontport.acceptance'] = payload
assert p.currentHistoryState() == before_history
""",
    )
    yield "lib-save", "font.save(str(Path(output) / 'lib.vfj'))"
    yield "lib-close", "font.close()"
    yield (
        "lib-reopen",
        "font = environment.OpenFont(str(Path(output) / 'lib.vfj'))\nbackend = font._backend",
    )
    yield (
        "lib-reopen-check",
        "assert font.lib['org.fontlab.fontport.acceptance'] == payload",
    )
    yield (
        "lib-delete",
        """
del font.lib['org.fontlab.fontport.acceptance']
observed = backend.get_lib()
assert 'org.fontlab.fontport.acceptance' not in observed, 'owned key deletion failed'
result = compare_lib(lib_before, observed)
result['boundary'] = 'foreign data after VFJ save/reopen and owned-key deletion'
""",
    )
    yield "lib-clear-seed", "font.lib['org.fontlab.fontport.acceptance'] = payload"
    yield (
        "lib-clear",
        "clear_before = backend.get_lib()\nfont.lib.clear()\nassert backend.get_lib() == {}",
    )
    yield "lib-clear-undo", "action('actionUndo')"
    yield "lib-clear-undo-check", "assert backend.get_lib() == clear_before"
    yield (
        "lib-nested-foreign-edit",
        """
nested = font.lib.get('fontport.probe.nested')
if isinstance(nested, dict):
    nested['valid'] = 2
    font.lib['fontport.probe.nested'] = nested
result = compare_lib({'nested': {**foreign['fontport.probe.nested'], 'valid': 2}},
                     {'nested': font.lib.get('fontport.probe.nested')})
result['boundary'] = 'nested foreign data after VFJ save/reopen and valid sibling edit'
if not isinstance(nested, dict):
    result['edit_skipped'] = 'VFJ did not retain the nested mapping'
""",
    )
    yield from feature_phases()
    yield (
        "export-one-glyph",
        "export_ufo_subset(backend, ['A'], Path(output) / 'source.ufo', family_name='Owned GetGo Sample')",
    )
    yield from batch_phases()
    yield "close-medi", "font.close()"
    yield "open-plum", "font = environment.OpenFont(paths['plum'])"
    yield (
        "native-designspace",
        """
model = Designspace.from_native(font._backend)
assert model.axes and len(model.sources) > 1
result = {'axes': [axis.name for axis in model.axes], 'masters': [entry.name for entry in model.sources],
          'instances': [entry.name for entry in model.instances]}
""",
    )
    yield "close-plum", "font.close()"
