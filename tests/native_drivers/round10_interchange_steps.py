# this_file: tests/native_drivers/round10_interchange_steps.py
"""27.4 export one glyph/info field per call; serialization is on the client."""


def start():
    return "from fontlab_fontport.interchange import ExportSession\nexport_session=ExportSession(backend)\nexport_steps=iter(export_session.steps())\nresult={'started':True,'losses':export_session.losses}"


def next_step():
    return """
from fontTools.ufoLib.glifLib import writeGlyphToString
import base64,plistlib
try:
    unit=next(export_steps)
except StopIteration:
    result={'complete':True,'losses':export_session.losses}
else:
    result={'complete':False,**unit}
    if unit['kind']=='glyph':
        g=export_session.font.layers[unit['layer']][unit['name']]
        result['glif']=writeGlyphToString(g.name,g,g.drawPoints)
    elif unit['kind']=='info':
        result['value']=getattr(export_session.font.info,unit['name'])
    elif unit['kind']=='features':
        result['value']=export_session.font.features.text
        result['lib_plist']=base64.b64encode(plistlib.dumps(dict(export_session.font.lib))).decode('ascii')
    elif unit['kind']=='kerning':
        result['value']=[(list(pair),value) for pair,value in export_session.font.kerning.items()]
    elif unit['kind']=='groups':
        result['value']=dict(export_session.font.groups)
    elif unit['kind']=='lib':
        result['value']=base64.b64encode(plistlib.dumps(dict(export_session.font.lib))).decode('ascii')
"""


def import_phases(path):
    yield (
        "import-open-ufo",
        f"from ufoLib2 import Font\nfrom fontlab_fontport.interchange import ImportSession\nimport_source=Font.open({str(path)!r},lazy=True)\nimport_plan=ImportSession(import_source,native=True)\nimport_checks=iter(import_plan.preflight_steps())\nresult={{'opened':True}}",
    )


def compare_phases(names, prefix):
    for name in names:
        yield (
            prefix + "-" + name,
            f"from round10_interchange_steps import glyph_receipt\nexpected=import_plan.staged[{name!r}]\nobserved=imported._backend.read_glyph({name!r},imported._backend.default_layer())\nresult=glyph_receipt(expected,observed)",
        )
    yield (
        prefix + "-metadata",
        "from fontlab_fontport.interchange import BLOCKS_KEY\nexpected=import_plan.staged\nib=imported._backend\nobserved={'groups':ib.get_groups(),'kerning':ib.get_kerning(),'features':ib.get_features(),'lib':ib.get_lib()}\nexpected_groups={k:tuple(v) for k,v in expected.groups.items()}\nexpected_lib={k:v for k,v in expected.lib.items() if k!=BLOCKS_KEY}\nresult={'equal':observed['groups']==expected_groups and observed['kerning']==expected.kerning and observed['features']==expected.features.text and observed['lib']==expected_lib,'groups':observed['groups'],'kerning':[(list(k),v) for k,v in observed['kerning'].items()],'features':observed['features'],'lib':observed['lib']}",
    )


def glyph_receipt(expected, observed):
    """Compare numbers by value and empty notes semantically; retain raw values."""
    from fontlab_fontport.recipes import digest

    fields = ("width", "height", "unicodes", "note", "lib")
    left = {key: getattr(expected, key, None) for key in fields}
    right = {key: getattr(observed, key, None) for key in fields}
    expected_digest, observed_digest = digest(expected), digest(observed)
    expected_anchors = [dict(a) for a in expected.anchors]
    observed_anchors = [dict(a) for a in observed.anchors]
    return {
        "equal": (
            expected_digest == observed_digest
            and all(
                ("" if left[key] is None else left[key]) == ("" if right[key] is None else right[key])
                if key == "note" else left[key] == right[key]
                for key in fields
            )
            and expected_anchors == observed_anchors
        ),
        "expected_digest": expected_digest,
        "observed_digest": observed_digest,
        "expected": left,
        "observed": right,
        "expected_anchors": expected_anchors,
        "observed_anchors": observed_anchors,
        "comparison_notes": [
            "fontlab.note.empty: absent/None and empty note are equivalent",
            "fontlab.numericValue: numbers compare by value without tolerance",
        ],
    }
