# this_file: tests/native_drivers/round10_common_steps.py
"""Raw owned-glyph receipts; Undo/Redo and persistence are separate host calls."""


def mutation_phases(label, code, *, name="fontport_probe", expected_capability=None, require_geometry_change=False, history_scope="glyph"):
    yield (
        label + "-baseline",
        f"history_scope={history_scope!r}\nprobe_name={name!r}\nbefore=payload(probe_name)\nbefore_geometry=geometry_snapshot(before)\ncontrol_before=payload('V')\nhistory_before=history(probe_name)\nhistory_rows_before=len((package_history(backend) if history_scope=='package' else glyph_history(backend,probe_name))['rows'])\nresult={{'payload':before,'control':control_before,'history':history_before}}",
    )
    yield (
        label + "-edit",
        f"edit_result=edit_receipt({code!r}, expected_capability={expected_capability!r})\nresult=edit_result",
    )
    yield (
        label + "-read",
        f"after=payload(probe_name)\nafter_geometry=geometry_snapshot(after)\ngeometry_changed_when_required=not {require_geometry_change!r} or not supported or before_geometry!=after_geometry\nresult={{'geometry_changed_when_required':geometry_changed_when_required,'payload':after,'history':history(probe_name),'control_unchanged':payload_equal(payload('V'),control_before),'refusal_unchanged':None if supported else (payload_equal(after,before) and history(probe_name)==history_before)}}",
    )
    yield (
        label + "-undo",
        "result=action('actionUndo') if supported else {'skipped':'pre-write refusal'}",
    )
    yield (
        label + "-undo-read",
        "observed=payload(probe_name)\nresult={'payload':observed,'equal':payload_equal(observed,before),'expected':before,**geometry_receipt(observed,before_geometry)}",
    )
    yield (
        label + "-undo-checkpoint",
        "result=action('actionUndo') if supported and edit_result.get('history_capability') else {'skipped':'no extra checkpoint'}",
    )
    yield (
        label + "-undo-checkpoint-read",
        "observed=payload(probe_name)\nresult={'payload':observed,'equal':payload_equal(observed,before),**geometry_receipt(observed,before_geometry)}",
    )
    yield (
        label + "-redo-checkpoint",
        "result=action('actionRedo') if supported and edit_result.get('history_capability') else {'skipped':'no extra checkpoint'}",
    )
    yield (
        label + "-redo-checkpoint-read",
        "observed=payload(probe_name)\nresult={'payload':observed,'equal':payload_equal(observed,before),**geometry_receipt(observed,before_geometry)}",
    )
    yield (
        label + "-redo",
        "result=action('actionRedo') if supported else {'skipped':'pre-write refusal'}",
    )
    yield (
        label + "-redo-read",
        "observed=payload(probe_name)\nresult={'payload':observed,'equal':payload_equal(observed,after),'expected':after,**geometry_receipt(observed,after_geometry)}",
    )
    yield (
        label + "-save",
        f"saved_path=str(Path(output)/{label + '.vfj'!r})\nfont.save(saved_path)\nresult={{'path':saved_path}}",
    )
    yield label + "-close", "font.close()\nresult={'closed':True}"
    yield (
        label + "-reopen",
        "font=environment.OpenFont(saved_path)\nbackend=font._backend\nowned_ids.add(backend.font_id)\nresult={'id':backend.font_id}",
    )
    yield (
        label + "-reopen-read",
        "observed=payload(probe_name)\nresult={'payload':observed,'equal':payload_equal(observed,after),'expected':after,**geometry_receipt(observed,after_geometry)}",
    )


SETUP = """
from pathlib import Path
from copy import deepcopy
import fontpr, fontlab
from PythonQt import QtGui
from fontlab_fontport.world import FontWorld
from fontlab_fontport.errors import UnsupportedCapability
from round10_payloads import payload_equal, geometry_snapshot, geometry_receipt
from round10_history import glyph_history, package_history
environment=FontWorld()
owned_ids=set()
def create_owned_backend():
    new=environment.NewFont()
    owned_ids.add(new._backend.font_id)
    return new._backend
def payload(name):
    g=backend._package().findName(name)
    if g is None or g.isNull:
        return None
    return deepcopy(fontpr.call('get_glyph',font_id=backend.font_id,glyph_name=name))
def history(name=None):
    return backend._package().currentHistoryState() if name is None or globals().get("history_scope")=="package" else glyph_history(backend,name)["index"]
def action(name):
    fontpr.call('set_active_font',font_id=backend.font_id)
    active=fontpr.call('get_active_font')
    control=fontlab.MainWindow().findChild(QtGui.QAction,name)
    if control is None or not control.enabled:
        return {'available':False,'equal':False,'action':name}
    control.trigger()
    return {'available':True,'action':name,'active':active,'owned_font_id':backend.font_id}
def edit_receipt(code,expected_capability=None):
    global supported
    supported=False
    try:
        exec(code,globals())
        supported=True
        observed_history=package_history(backend) if globals().get("history_scope")=="package" else glyph_history(backend,probe_name)
        rows_after=len(observed_history["rows"])
        return {'history_scope':globals().get('history_scope','glyph'),'supported':True,'history':history(probe_name),'history_before':history_before,'one_history_row':rows_after==history_rows_before+1,'history_protocol_matches':rows_after-history_rows_before in (1,2),'history_capability':'glyph.exactSingleUndo' if rows_after-history_rows_before==2 else None,'expected_refusal':expected_capability,'capability_matches_expectation':expected_capability is None,'rows_before':history_rows_before,'rows_after':rows_after,'glyph_history':observed_history}
    except UnsupportedCapability as error:
        return {'supported':False,'capability':error.capability,'reason':str(error),'expected_refusal':expected_capability,'capability_matches_expectation':expected_capability is not None and error.capability==expected_capability}
    except Exception as error:
        import traceback
        return {'status':'unclassified','supported':False,'error':str(error),'type':type(error).__name__,'traceback':traceback.format_exc()}
result={'setup':True}
"""
