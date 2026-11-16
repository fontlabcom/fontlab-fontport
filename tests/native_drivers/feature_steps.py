# this_file: tests/native_drivers/feature_steps.py
"""Real B08 structured edit/Undo/VFJ receipts, one bounded native call per phase."""


def feature_phases():
    yield (
        "feature-baseline",
        """
import json
from hashlib import sha256
from fontlab_fontport.native_features import read_info, blocks_from_info, text_from_blocks
from fontlab_fontport.errors import UnsupportedCapability
feature_info_before = read_info(backend.font_id)
feature_rows_before = deepcopy(feature_info_before.get('openTypeFeatures', []))
feature_classes_before = deepcopy(feature_info_before.get('classes', []))
feature_blocks_before = blocks_from_info(feature_info_before)
def feature_hash(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
def feature_receipt(info, expected):
    rows = deepcopy(info.get('openTypeFeatures', []))
    classes = deepcopy(info.get('classes', []))
    whole_text = ''.join(row.get('feature', '') for row in rows)
    expected_text = ''.join(row.get('feature', '') for row in expected)
    return {'rows_equal': rows == expected,
            'whole_text_equal': whole_text == expected_text,
            'classes_equal': classes == feature_classes_before,
            'openTypeFeatures': rows, 'classes': classes, 'whole_text': whole_text,
            'sha256': feature_hash(rows), 'expected_sha256': feature_hash(expected),
            'classes_sha256': feature_hash(classes),
            'expected_classes_sha256': feature_hash(feature_classes_before),
            'whole_text_sha256': sha256(whole_text.encode('utf-8')).hexdigest(),
            'expected_whole_text_sha256': sha256(expected_text.encode('utf-8')).hexdigest()}
result = {'supported': True, 'has_named_features': bool(feature_blocks_before['features']),
          'openTypeFeatures': feature_rows_before,
          'classes': feature_classes_before, 'metadata_bytes': len(json.dumps(feature_info_before))}
""",
    )
    yield (
        "feature-read-text",
        """
observed_text = font.features.text
expected_text = text_from_blocks(feature_blocks_before)
result = {'whole_text_equal': observed_text == expected_text, 'whole_text': observed_text,
          'whole_text_sha256': sha256(observed_text.encode('utf-8')).hexdigest(),
          'expected_whole_text_sha256': sha256(expected_text.encode('utf-8')).hexdigest()}
""",
    )
    yield (
        "feature-stage",
        """
feature_blocks_after = deepcopy(feature_blocks_before)
tag = None
if feature_blocks_after['features']:
    tag, code = feature_blocks_after['features'][0]
    feature_blocks_after['features'][0] = (tag, code + '\\r\\n# Fontport owned B08 edit Ω 日本語\\r\\n')
feature_rows_after = ([{'feature': feature_blocks_after['prefix']}] if feature_blocks_after['prefix'] else [])
feature_rows_after += [{'name': tag, 'feature': code} for tag, code in feature_blocks_after['features']]
result = {'edited_tag': tag, 'staged_only': True, 'edit_available': tag is not None}
""",
    )
    yield (
        "feature-noop",
        """
feature_history = backend._package().currentHistoryState()
feature_noop_error = None
try:
    font.features.set_blocks(feature_blocks_before)
except Exception as error:
    feature_noop_error = {'type': type(error).__name__, 'message': str(error)}
feature_history_after = backend._package().currentHistoryState()
result = {'no_history_for_identical_blocks': feature_history_after == feature_history,
          'identical_write_succeeded': feature_noop_error is None,
          'history_before': feature_history, 'history_after': feature_history_after,
          'write_error': feature_noop_error}
""",
    )
    yield (
        "feature-split-refusal",
        """
feature_history = backend._package().currentHistoryState()
feature_refusal = None
feature_refused_correctly = False
try:
    backend.set_features('# arbitrary new source\\nfeature liga {} liga;\\n')
except Exception as error:
    feature_refusal = {'type': type(error).__name__, 'message': str(error),
                       'capability': getattr(error, 'capability', None)}
    feature_refused_correctly = (isinstance(error, UnsupportedCapability)
                                and error.capability == 'font.features.text.split')
feature_history_after = backend._package().currentHistoryState()
result = {'only_arbitrary_split_refused': feature_refused_correctly,
          'no_history_for_split_refusal': feature_history_after == feature_history,
          'history_before': feature_history, 'history_after': feature_history_after,
          'refusal': feature_refusal}
""",
    )
    yield (
        "feature-synthesis-refusal",
        """
feature_history = backend._package().currentHistoryState()
synthesis_blocks = deepcopy(feature_blocks_before)
synthesis_blocks['prefix'] = ''
synthesis_refusal = None
synthesis_refused = False
try:
    backend.set_feature_blocks(synthesis_blocks)
except Exception as error:
    synthesis_refusal = {'type': type(error).__name__, 'message': str(error)}
    synthesis_refused = isinstance(error, ValueError) and '#> languagesystem' in str(error)
feature_history_after = backend._package().currentHistoryState()
result = {'implicit_languagesystem_refused': synthesis_refused,
          'no_history_for_synthesis_refusal': feature_history_after == feature_history,
          'history_before': feature_history, 'history_after': feature_history_after,
          'refusal': synthesis_refusal}
""",
    )
    yield (
        "feature-apply",
        "font.features.set_blocks(feature_blocks_after)\nresult = {'applied': True}",
    )
    yield (
        "feature-readback",
        "result = feature_receipt(read_info(backend.font_id), feature_rows_after)",
    )
    yield "feature-undo", "action('actionUndo')"
    yield (
        "feature-undo-readback",
        "result = feature_receipt(read_info(backend.font_id), feature_rows_before)",
    )
    yield "feature-redo", "action('actionRedo')"
    yield (
        "feature-redo-readback",
        "result = feature_receipt(read_info(backend.font_id), feature_rows_after)",
    )
    yield "feature-save", "font.save(str(Path(output) / 'features.vfj'))"
    yield "feature-close", "font.close()"
    yield (
        "feature-reopen",
        "font = environment.OpenFont(str(Path(output) / 'features.vfj'))\nbackend = font._backend",
    )
    yield (
        "feature-reopen-readback",
        "result = feature_receipt(read_info(backend.font_id), feature_rows_after)",
    )
    yield "feature-restore", "font.features.set_blocks(feature_blocks_before)"
    yield (
        "feature-restore-save",
        "font.save(str(Path(output) / 'features-restored.vfj'))",
    )
    yield "feature-restore-close", "font.close()"
    yield (
        "feature-restore-reopen",
        "font = environment.OpenFont(str(Path(output) / 'features-restored.vfj'))\nbackend = font._backend",
    )
    yield (
        "feature-restore-readback",
        "result = feature_receipt(read_info(backend.font_id), feature_rows_before)",
    )
