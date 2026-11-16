---
this_file: src_docs/md/guides/FONTPARTS-COVERAGE.md
---

# FontParts yardstick and RoboFab mapping

Regenerate the complete
per-ID ledger with `uv run python tools/fontparts-coverage.py --reuse-parity`.
Omit --reuse-parity to re-run host-free parity. Supply --native-evidence with
the round14 directory when outside the workspace; the default searches ancestors.

Host-free parity uses FontParts 1.1.1, which exposes **fontParts.test.testEnvironment**
(singular `test`), with 1,797 IDs. Real upstream fontshell: 1,796 pass, one
upstream skip (`TestImage.test_bool_data_len_zero`: “Cannot set zero data”).
The live-font/UFO-backend run: 1,748 pass, 48 UnsupportedCapability, the same
skip, **zero unclassified failures**. Pytest checks every ID and prevents new
capability exclusions without updating the reviewed 48-ID baseline.

These counts are not native passes. The per-ID fixtures column distinguishes
real live RFont/UFOBackend objects from upstream's detached fontshell objects.
The latter are parity checks, not FontGate fixtures. No package namespace is
impersonated. Full raw tracebacks/fixture routes are retained in
`verification/issue-105/round10/{fontshell,memory}.jsonl`.

The native callable is `fontlab_fontport.testing.object_generator(cls_name)`:

The examples require installed `fontlab-fly>=1.3.0` and their canonical providers.

```python
from fontParts.test import testEnvironment
from fly.fp.testing import ObjectGenerator, generator_context, object_generator

with generator_context(ObjectGenerator()):
    passed = testEnvironment(object_generator, inApp=True)
```

Do not run that monolithic invocation through run_python. C4 uses round10.py
instead: one upstream ID per RPC, followed by separate per-owner cleanup RPCs.
Use `--native-attached` for the attached upstream column (default: orphan column).
Each column is observed independently. The f3d7dc5 run separately counts the exact
72 C4-reviewed orphan/parent IDs as HarnessExclusion with capability
`testing.nativeAttached.parents` in attached mode only. The reviewed ID list is
in testing_exclusions.py; no assertion text is classified heuristically. All
other assertions/bare NotImplementedError remain unclassified failures. The native driver first exercises `ObjectGenerator(native_attached=True)` for
all 16 families. Every native document is created/owned, tracked before wrapper
construction, and closed with `close_font(save=False)` on the finally path.
Guideline/image creation returns explicit capability refusals.

Upstream's ordinary object generator requires **orphans** with no parent. This
adapter currently binds registered documents; detached native wrappers are not
implemented. This is an adapter limit, not a claim that FontGate has no detached
object API. Native orphan requests refuse
as `testing.nativeOrphan.<family>`; attached fixtures must not be presented as
passing those parent assertions. Selection is also explicitly unavailable.
Native font tests exercise real registered documents. Native assertions and
unexpected errors remain failures with tracebacks; the controller never calls
them host defects merely because FontLab was involved. C4 must attach a minimal
`--test-id` reproducer and an upstream fl issue to any confirmed host defect.

C4's **f3d7dc5 / FontLab 9.0.9783** native run classifies all 1,797 IDs in
both modes: **orphan 432 pass / 1,365 named capability / 0 unclassified**;
**attached 1,087 pass / 638 named capability / 72 harness exclusions /
0 unclassified**. These are C4 observations, not a host-free lane's native run.
Source: workspace `verification/issue-106/evidence/issue-105/round14/SUMMARY.md`,
`upstream-out/20261016T043446540472Z-49425680/{receipts.jsonl,result.json}` and
`upstream-attached-out/20261016T043701928259Z-14a1ddd8/{receipts.jsonl,result.json}`.
There are no separate round14 classification JSON files: the generator consumes
the actual per-ID classifications in receipts and reconciles both result counts.
It rejects missing/duplicate IDs, unnamed capabilities and unclassified results.
Pass/capability/harness are separate outcomes; parent harness exclusions are
not product failures or native passes. Row 30.1 closure remains controller-owned.
The driver exits nonzero for any unclassified result, mismatch or slow phase.
Its trace guard checks Python work; a blocking native call cannot be preempted.
Any phase reaching four seconds needs a C4 ticket and further splitting.

## RoboFab FL6 checklist → current tests

Names below use prefix `fontParts.test.`. The full ledger provides each exact
ID, result and fixture surface. “Parity” below always means host-free parity.
Every native-boundary cell below is scoped to the measured f3d7dc5 state in
C4's `verification/issue-106/evidence/issue-105/round14/SUMMARY.md`; exact per-ID
capabilities are in the ledger. Additional component detail comes from
`glyph-out/20261016T043125022947Z-4b1827c9/receipts.jsonl` in that same round14
folder: `glyph-component-replace-edit` is supported=False / glyph.geometry,
so its later equal flags prove unchanged refused data, not replacement support.

| Legacy item | Current equivalent and passing upstream ID | Native boundary |
|---|---|---|
| Anchor append shape | `test_glyph.TestGlyph.test_appendAnchor_valid_object`; `examples/fontparts/04_anchors.py`; `tests/test_host.py` anchor preflight | Integral anchor edits have equal Undo/Redo/reopen receipts. Fractional anchors refuse by name; color/identifier limits appear per ID. |
| `RFont.update()` / `RGlyph.update()` | `test_deprecated.TestDeprecated.test_font_deprecated_update` / `test_glyph_deprecated_update` check dispatch to `changed()` | Live write/Undo protocol is measured; external-edit cache notifications remain unsupported and require refresh/reacquisition. Deprecated update dispatch does not prove external coherence. |
| `clearContours` | `test_glyph.TestGlyph.test_clearContours`; example 03 | Clear and contour edits restore geometry on first Undo and Redo/reopen. Two rows include a named no-op checkpoint (glyph.exactSingleUndo); hinted edits refuse unchanged. |
| H/V guide helpers | `test_guideline.TestGuideline.test_angle_get_generic`, `test_angle_set_valid_zero_generic`; `test_glyph.TestGlyph.test_clearGuidelines` / `test_appendGuideline_valid_object` | Native guideline writes remain named capabilities in the attached ledger. Angle/clear/remove API parity does not supply the old H/V helper names. |
| RFont / RLayer / RGlyph | All `test_font.TestFont`, `test_layer.TestLayer`, `test_glyph.TestGlyph` rows below | Owned font/glyph lifecycle and 19 world examples pass; topology/rename/delete limits remain named per-ID capabilities. This does not turn all family tests into native passes. |
| RContour / RSegment / RPoint / RBPoint | All `test_contour`, `test_segment`, `test_point`, `test_bPoint` rows | Attached point/segment/contour edits have no unclassified failures; measured live pen/appendPoint geometry restores through Undo. Detached parent requirements are separately counted harness exclusions. |
| RComponent.copy | `test_component.TestComponent.test_copy_seperate_objects`, `test_copy_same_transformation` | Add and transform have equal native Undo/Redo/reopen geometry. Replacement is explicitly refused as glyph.geometry in the edit receipt; equal follow-up reads confirm unchanged data. Removal is not demonstrated as supported. |
| RAnchor / RGuide.angle | All `test_anchor` / `test_guideline` rows; `test_guideline.TestGuideline.test_angle_set_valid_positive_float` | Integral anchors are measured; fractional/color/identifier and native guide writes retain named limits. Float-angle parity is not native guide persistence. |
| RGroups / RKerning.update | All `test_groups`, `test_kerning` rows; `test_kerning.TestKerning.test_set_glyph_glyph` | Integer kerning/groups and owned examples pass; fractional history, Unicode classes, divergent both-sided and legacy-persistence cases refuse by name with unchanged history. Multi-membership setup is fixed. |
| RLib / RInfo / RFeatures | All `test_lib`, `test_info`, `test_features` rows | Supported info and structured fields have equal read/Undo/Redo/VFJ receipts on the key master; name-record changes refuse. Lib/features pass where shown by the native per-ID ledger; capabilities are not passes. |
| `_startNodeIndex` / `_nakedParent` | `test_contour.TestContour.test_setStartPoint`, `test_setStartSegment_index`, `test_index` | Public start/index operations use actual attached contours; their individual results are recorded below. Orphan/replaceable-parent assertions remain explicit harness exclusions. |
| FL-only GetMetrics/SetMetrics/GetBoundingRect/fontIndex | FontParts metrics/bounds/parent objects; BoundsPen recipe | 104 native glyph digest/control-bounds checks pass; BoundsPen curve extrema remain distinct from native control bounds. No FL5 indexes or compatibility aliases are invented. |
| Hint conversion helpers | No upstream FontParts PostScriptGlyphHintValues equivalent | Hinted Medio exclam edits refuse glyph.geometry with unchanged payload/history. Hint conversion/writes remain outside the supported FontParts surface. |
| Point/segment/contour/glyph selection | Selection tests in the full ledger | Native/world selection remains a named capability refusal; world registration/open/new/close and all 19 examples pass. |
| File dialogs | Outside Fontport (Vanilla session moved to Glyport, `fontlab_glyport.ui.session`) | The f3d7dc5 upstream/world suites do not prove interactive dialogs. Fontport holds no dialog code; Glyport owns that verification. |

Python 2 RoboFab source is reference material. Fontport uses the actual Python
3 upstream packages. The method inventory is mapped without treating detached
passes as completion of the native environment.

## Per-test ledger

Versions: fontParts 1.1.1, defcon 0.12.2, fontPens 0.4.0, fontTools 4.67.0, ufoLib2 0.19.1.

| Upstream test ID | fontshell parity | Live-font / detached-orphan result | Fixtures actually used | Native orphan C4 | Native attached C4 |
|---|---|---|---|---|---|
| `fontParts.test.test_anchor.TestAnchor.test_color_get_none` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_color_set_invalid_int` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_color_set_invalid_over_max` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_color_set_invalid_string` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_color_set_invalid_too_few` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_color_set_invalid_uner_min` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_color_set_none` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_color_set_valid_decimal` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_color_set_valid_max` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_color_set_valid_min` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_copy_generated_identifier_different` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_copy_same_color` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_copy_same_identifier` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_copy_same_name` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_copy_same_x` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_copy_same_y` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_copy_seperate_objects` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_get` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_get_index` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_anchor.TestAnchor.test_get_index_noParent` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_anchor.TestAnchor.test_get_parent_font` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_anchor.TestAnchor.test_get_parent_glyph` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_anchor.TestAnchor.test_get_parent_layer` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_anchor.TestAnchor.test_get_parent_noFont` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_anchor.TestAnchor.test_get_parent_noGlyph` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_anchor.TestAnchor.test_get_parent_noLayer` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_anchor.TestAnchor.test_hash_object_other` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_hash_object_other_variable_assignment` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_hash_object_self` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_hash_object_self_variable_assignment` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_identifier_cannot_set` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_identifier_consistency` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: identifiers |
| `fontParts.test.test_anchor.TestAnchor.test_identifier_force_set` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: identifiers |
| `fontParts.test.test_anchor.TestAnchor.test_identifier_generated_type` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: identifiers |
| `fontParts.test.test_anchor.TestAnchor.test_identifier_get_none` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_is_hashable` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_moveBy_invalid_all_strings_value` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_moveBy_invalid_int_value` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_moveBy_invalid_one_string_value` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_moveBy_valid` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_object_equal_self` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_object_equal_variable_assignment_self` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_object_not_equal_other` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_object_not_equal_variable_assignment_other` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_reprContents` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_reprContents_color` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_reprContents_noGlyph` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_reprContents_noGlyph_color` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.metadata |
| `fontParts.test.test_anchor.TestAnchor.test_rotateBy_invalid_string_value` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_rotateBy_invalid_too_large_value_negative` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_rotateBy_invalid_too_large_value_positive` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_rotateBy_valid_no_origin` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.precision |
| `fontParts.test.test_anchor.TestAnchor.test_rotateBy_valid_origin` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_round_at_half` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.precision |
| `fontParts.test.test_anchor.TestAnchor.test_round_close_to` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.precision |
| `fontParts.test.test_anchor.TestAnchor.test_scaleBy_invalid_one_string_value` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_scaleBy_invalid_tuple_too_many_values` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_scaleBy_invalid_two_string_values` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_scaleBy_valid_one_value_no_origin` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_scaleBy_valid_two_values_no_origin` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_scaleBy_valid_two_values_origin` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_selected_false` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_selected_true` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_set_index_negative` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_anchor.TestAnchor.test_set_index_noParent` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_set_index_positive` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_anchor.TestAnchor.test_set_invalid` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_set_none` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.name |
| `fontParts.test.test_anchor.TestAnchor.test_set_parent_glyph` | pass | pass | anchor=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_anchor.TestAnchor.test_set_parent_glyph_exists` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_anchor.TestAnchor.test_set_parent_glyph_none` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_anchor.TestAnchor.test_set_valid` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_skewBy_valid_no_origin_one_value` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.precision |
| `fontParts.test.test_anchor.TestAnchor.test_skewBy_valid_no_origin_two_values` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.precision |
| `fontParts.test.test_anchor.TestAnchor.test_skewBy_valid_origin_one_value` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_skewBy_valid_origin_two_values` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_transformBy_invalid_all_string_values` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_transformBy_invalid_int_value` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_transformBy_invalid_one_string_value` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_transformBy_valid_no_origin` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_transformBy_valid_origin` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_x_get` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_x_set_invalid_none` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_x_set_valid_negative` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_x_set_valid_negative_decimal` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.precision |
| `fontParts.test.test_anchor.TestAnchor.test_x_set_valid_positive` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_x_set_valid_positive_decimal` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.precision |
| `fontParts.test.test_anchor.TestAnchor.test_x_set_valid_string` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_x_set_valid_zero` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_y_get` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_y_set_invalid_none` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_y_set_valid_negative` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_y_set_valid_negative_decimal` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.precision |
| `fontParts.test.test_anchor.TestAnchor.test_y_set_valid_positive` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_y_set_valid_positive_decimal` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: glyph.anchor.precision |
| `fontParts.test.test_anchor.TestAnchor.test_y_set_valid_string` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_anchor.TestAnchor.test_y_set_valid_zero` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_copy_different_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_copy_none_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_copy_seperate_objects` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_getIdentifer_consistency` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_bPoint.TestBPoint.test_get_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_bcpIn_corner` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_bcpIn_curve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_bcpOut_corner` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_bcpOut_curve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_index` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_font` | pass | pass | contour=fontshell-parity, font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_font_noContour` | pass | pass | bPoint=fontshell-parity | capability: testing.nativeOrphan.bPoint | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_glyph` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_glyph_noContour` | pass | pass | bPoint=fontshell-parity | capability: testing.nativeOrphan.bPoint | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_layer` | pass | pass | contour=fontshell-parity, layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_layer_noContour` | pass | pass | bPoint=fontshell-parity | capability: testing.nativeOrphan.bPoint | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_nextSegment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_noContour` | pass | pass | bPoint=fontshell-parity | capability: testing.nativeOrphan.bPoint | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_noFont` | pass | pass | contour=fontshell-parity, layer=fontshell-parity | capability: testing.nativeOrphan.layer | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_noGlyph` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_noLayer` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_noNextSegment` | pass | pass | bPoint=fontshell-parity | capability: testing.nativeOrphan.bPoint | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_bPoint.TestBPoint.test_get_parent_segment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_type_corner` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_get_type_curve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_hash` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_identifier_cannot_set` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_identifier_consistency` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_bPoint.TestBPoint.test_identifier_generated_type` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_bPoint.TestBPoint.test_identifier_get_none` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_invalid_one_string_value_scaleBy` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_invalid_tuple_too_many_values_scaleBy` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_invalid_two_string_values_scaleBy` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_moveBy_invalid_all_strings_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_moveBy_invalid_int_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_moveBy_invalid_one_string_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_moveBy_noChange_bcpIn` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_moveBy_noChange_bcpOut` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_moveBy_valid_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_object_equal_self` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_object_equal_self_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_object_not_equal_other` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_object_not_equal_other_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_reprContents` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_reprContents_noContour` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_rotateBy_invalid_string_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_rotateBy_invalid_too_large_value_negative` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_rotateBy_invalid_too_large_value_positive` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_rotateBy_valid_no_origin_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_rotateBy_valid_origin_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_rotateBy_valid_origin_bcpIn` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_rotateBy_valid_origin_bcpOut` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_round_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_round_bcpIn` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_round_bcpOut` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_scaleBy_valid_one_value_no_origin_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_scaleBy_valid_two_values_no_origin_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_scaleBy_valid_two_values_origin_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_scaleBy_valid_two_values_origin_bcpIn` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_scaleBy_valid_two_values_origin_bcpOut` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_selected_false` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_selected_true` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_already_set_parent_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_anchor_invalidType_None` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_anchor_invalidType_int` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_anchor_invalid_single_item_list` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_anchor_invalid_single_item_tuple` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_anchor_invalid_too_many_items` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_anchor_valid_list` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_anchor_valid_tuple` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpInOut_type_change` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpIn_corner_valid_tuple` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpIn_corner_with_bcpOut` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpIn_curve_firstPointOpenContour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpIn_curve_valid_tuple` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpIn_invalidType_None` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpIn_invalidType_int` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpIn_invalid_single_item_list` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpIn_invalid_single_item_tuple` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpIn_invalid_too_many_items` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpIn_valid_list` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOutIn_type_change` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOut_corner_valid_tuple` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOut_corner_with_bcpIn` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOut_curve_lastPointOpenContour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOut_curve_valid_tuple` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOut_invalidType_None` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOut_invalidType_int` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOut_invalid_single_item_list` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOut_invalid_single_item_tuple` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOut_invalid_too_many_items` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_bcpOut_valid_list` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_index` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_parent_contour` | pass | pass | bPoint=fontshell-parity, contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_bPoint.TestBPoint.test_set_parent_contour_none` | pass | pass | bPoint=fontshell-parity | capability: testing.nativeOrphan.bPoint | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_bPoint.TestBPoint.test_set_type_corner` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_set_type_curve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_skewBy_invalid_string_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_skewBy_invalid_too_large_value_negative` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_skewBy_invalid_too_large_value_positive` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_skewBy_valid_no_origin_one_value_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_skewBy_valid_no_origin_two_values_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_skewBy_valid_origin_one_value_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_skewBy_valid_origin_two_values_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_skewBy_valid_origin_two_values_bcpIn` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_skewBy_valid_origin_two_values_bcpOut` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_smooth_move_type_issue435` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_transformBy_invalid_all_string_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_transformBy_invalid_int_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_transformBy_invalid_one_string_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_transformBy_valid_no_origin_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_transformBy_valid_no_origin_bcpIn` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_transformBy_valid_no_origin_bcpOut` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_transformBy_valid_origin_anchor` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_transformBy_valid_origin_bcpIn` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_transformBy_valid_origin_bcpOut` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bPoint.TestBPoint.test_type_not_equal` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_bounds.TestBounds.test_height` | pass | pass | none | pass | pass |
| `fontParts.test.test_bounds.TestBounds.test_new_args` | pass | pass | none | pass | pass |
| `fontParts.test.test_bounds.TestBounds.test_new_kwargs` | pass | pass | none | pass | pass |
| `fontParts.test.test_bounds.TestBounds.test_new_tuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_bounds.TestBounds.test_width` | pass | pass | none | pass | pass |
| `fontParts.test.test_bounds.TestBounds.test_xCenter` | pass | pass | none | pass | pass |
| `fontParts.test.test_bounds.TestBounds.test_yCenter` | pass | pass | none | pass | pass |
| `fontParts.test.test_color.TestColor.test_new_args` | pass | pass | none | pass | pass |
| `fontParts.test.test_color.TestColor.test_new_kwargs` | pass | pass | none | pass | pass |
| `fontParts.test.test_color.TestColor.test_new_tuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_component.TestComponent.test_baseGlyph_generic` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_baseGlyph_invalid_set_empty_string` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_baseGlyph_invalid_set_int` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_baseGlyph_invalid_set_none` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_baseGlyph_valid_set` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_bounds_get` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_bounds_invalid_set` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_bounds_none` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: glyph.geometry |
| `fontParts.test.test_component.TestComponent.test_bounds_on_move` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_bounds_on_scale` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_copy_generated_identifier_different` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: identifiers |
| `fontParts.test.test_component.TestComponent.test_copy_not_identifier` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: identifiers |
| `fontParts.test.test_component.TestComponent.test_copy_same_baseGlyph` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_copy_same_offset` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_copy_same_scale` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_copy_same_transformation` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_copy_seperate_objects` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_decompose_digest` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: glyph.geometry |
| `fontParts.test.test_component.TestComponent.test_decompose_identifiers` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: identifiers |
| `fontParts.test.test_component.TestComponent.test_decompose_noParent` | pass | pass | component=fontshell-parity | capability: testing.nativeOrphan.component | capability: glyph.geometry |
| `fontParts.test.test_component.TestComponent.test_decompose_transformation` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: glyph.geometry |
| `fontParts.test.test_component.TestComponent.test_draw` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_drawPoints` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: identifiers |
| `fontParts.test.test_component.TestComponent.test_drawPoints_legacy` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: identifiers |
| `fontParts.test.test_component.TestComponent.test_get_index` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_get_index_noParent` | pass | pass | component=fontshell-parity | capability: testing.nativeOrphan.component | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_component.TestComponent.test_get_parent_font` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_component.TestComponent.test_get_parent_glyph` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_get_parent_layer` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_get_parent_noFont` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_get_parent_noGlyph` | pass | pass | component=fontshell-parity | capability: testing.nativeOrphan.component | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_component.TestComponent.test_get_parent_noLayer` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_hash_object_other` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_hash_object_other_variable_assignment` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_hash_object_self` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_hash_object_self_variable_assignment` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_identifier_cannot_set` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_identifier_consistency` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: identifiers |
| `fontParts.test.test_component.TestComponent.test_identifier_generated_type` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: identifiers |
| `fontParts.test.test_component.TestComponent.test_identifier_get_none` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_is_hashable` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_moveBy_invalid_all_strings_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_moveBy_invalid_int_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_moveBy_invalid_one_string_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_moveBy_valid` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_object_equal_assigned_variable` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_object_equal_self` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_object_not_equal_assigned_variable_other` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_object_not_equal_other` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_offset_generic` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_offset_invalid_set_bogus_real` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_offset_invalid_set_int` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_offset_invalid_set_none` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_offset_invalid_set_real_bogus` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_offset_valid_set_negative_negative` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_offset_valid_set_negative_positive` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_offset_valid_set_positive_negative` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_offset_valid_set_positive_positive` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_offset_valid_set_zero` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_pointInside_false` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_pointInside_true` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_reprContents` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_reprContents_noGlyph` | pass | pass | component=fontshell-parity | capability: testing.nativeOrphan.component | pass |
| `fontParts.test.test_component.TestComponent.test_rotateBy_invalid_string_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_rotateBy_invalid_too_large_value_negative` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_rotateBy_invalid_too_large_value_positive` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_rotateBy_valid_no_origin` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_rotateBy_valid_origin` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_round` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scaleBy_invalid_one_string_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scaleBy_invalid_tuple_too_many_values` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scaleBy_invalid_two_string_values` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scaleBy_valid_one_value_no_origin` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scaleBy_valid_two_values_no_origin` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scaleBy_valid_two_values_origin` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scale_generic` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scale_invalid_set_bogus_real` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scale_invalid_set_int` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scale_invalid_set_none` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scale_invalid_set_real_bogus` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scale_valid_set_negative_negative` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scale_valid_set_negative_positive` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scale_valid_set_positive_negative` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scale_valid_set_positive_positive` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_scale_valid_set_zero` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_selected_false` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_selected_true` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_set_index_negative` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_set_index_noParent` | pass | pass | component=fontshell-parity | capability: testing.nativeOrphan.component | capability: glyph.geometry |
| `fontParts.test.test_component.TestComponent.test_set_index_pastLength` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_set_index_positive` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_set_parent_glyph` | pass | pass | component=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_component.TestComponent.test_set_parent_glyph_exists` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_component.TestComponent.test_set_parent_glyph_none` | pass | pass | component=fontshell-parity | capability: testing.nativeOrphan.component | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_component.TestComponent.test_skewBy_valid_no_origin_one_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_skewBy_valid_no_origin_two_values` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_skewBy_valid_origin_one_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_skewBy_valid_origin_two_values` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_transformBy_invalid_all_string_values` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_transformBy_invalid_int_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_transformBy_invalid_one_string_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_transformBy_valid_no_origin` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_transformBy_valid_origin` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_transformation_generic` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_transformation_invalid_set_member` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_transformation_invalid_set_none` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_transformation_valid_set_negative` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_component.TestComponent.test_transformation_valid_set_positive` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_contour.TestContour.test_appendBPoint_bPoint` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_appendBPoint_overrides` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_appendBPoint_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_appendPoint_bPoint` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_appendPoint_overrides` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_contour.TestContour.test_appendPoint_position` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_appendSegment_overrides` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_appendSegment_points` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_appendSegment_raises` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_appendSegment_segment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_area` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_bPoints_bPointClass_none` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_bounds_get` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_bounds_point_not_at_extrema` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_bounds_set_float` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_contourInside` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_copyData` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_drawPoints_oldProtocol` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_empty_area` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_empty_bounds` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_get_index_glyph` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_contour.TestContour.test_get_index_no_glyph` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_hash_object_other` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_hash_object_other_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_hash_object_self` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_hash_object_self_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_index` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_contour.TestContour.test_insertBPoint_bPoint` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_insertBPoint_overrides` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_insertBPoint_raises` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_insertBPoint_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_insertPoint_overrides` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_contour.TestContour.test_insertPoint_point` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_insertPoint_position` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_insertPoint_raises` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_insertSegment_overrides` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_insertSegment_raises` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_insertSegment_segment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_invalid_bounds_set` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_isCompatible_different_direction` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_isCompatible_different_open_closed` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_isCompatible_different_segment_count` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_isCompatible_incompatible_segments` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_isCompatible_multiple_issues` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_isCompatible_same_contours` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_is_hashable` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_iterSegment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_object_equal_self` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_object_equal_self_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_object_not_equal_self` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_object_not_equal_self_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_parent_font_get` | pass | pass | contour=fontshell-parity, font=live-font, glyph=fontshell-parity, layer=fontshell-parity | capability: testing.nativeOrphan.layer | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_parent_font_get_none` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_parent_font_set` | pass | pass | contour=fontshell-parity, font=live-font | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_parent_glyph_get` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_contour.TestContour.test_parent_glyph_get_none` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_parent_glyph_set_already_set` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_parent_glyph_set_glyph` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_parent_glyph_set_glyph_None` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_parent_layer_get` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity, layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_contour.TestContour.test_parent_layer_get_none` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_parent_layer_set` | pass | pass | contour=fontshell-parity, layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_contour.TestContour.test_pointInside` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_removeBPoint_bPoint` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_removeBPoint_index` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_removeBPoint_index_out_of_range` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_removeBPoint_offcurves` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_removePoint_index_out_of_range` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_removeSegment_index` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_removeSegment_index_out_of_range` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_removeSegment_segment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_reprContents_Glyph_ID` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_reprContents_Glyph_noID` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_contour.TestContour.test_reprContents_noGlyph_ID` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_contour.TestContour.test_reprContents_noGlyph_noID` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_round` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segment_insert_closed` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segment_insert_curve_closed` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segment_insert_curve_open` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segment_insert_open` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segments_empty` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segments_offcurves_begin` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segments_offcurves_begin_end` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segments_offcurves_end` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segments_offcurves_middle` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segments_segmentClass_none` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_segments_start_move_offcurves_end` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedBPoints_default` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedBPoints_setEmptyList` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedBPoints_setFilledList` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedBPoints_setSubObject` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedPoints_default` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedPoints_setEmptyList` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedPoints_setFilledList` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedPoints_setSubObject` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedSegments_default` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedSegments_setEmptyList` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedSegments_setFilledList` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selectedSegments_setSubObject` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selected_false` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_selected_true` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_setStartPoint` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_setStartPoint_index_out_of_range` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_setStartPoint_index_zero` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_setStartPoint_open_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_setStartSegment_index` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_setStartSegment_index_out_of_range` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_setStartSegment_open_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_setStartSegment_segment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_set_clockwise` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_contour.TestContour.test_set_index` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_contour.TestContour.test_set_index_negative_value` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_contour.TestContour.test_set_index_none` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_contour.TestContour.test_set_index_orphan_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated__generateIdentifer` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_generateIdentifer` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_getParent` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_move` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_rotate_no_offset` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.anchor.precision |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_rotate_offset` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.anchor.precision |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_scale_center` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_scale_no_center` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_setChanged` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_skew_no_offset_one_value` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.anchor.precision |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_skew_no_offset_two_values` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.anchor.precision |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_skew_offset_one_value` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.anchor.precision |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_skew_offset_two_values` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.anchor.precision |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_transform` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_translate` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_deprecated_update` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_removed_draw` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_removed_drawPoints` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_anchor_removed_setParent` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated__generateIdentifier` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_generateIdentifier` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_move` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_rotate_no_offset` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_rotate_offset` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_scale_center` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_scale_no_center` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_setChanged` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_skew_no_offset_one_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_skew_no_offset_two_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_skew_offset_one_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_skew_offset_two_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_transform` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_translate` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_deprecated_update` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_getParent` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_removed_select` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_bPoint_removed_setParent` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated__generateIdentifier` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated__get_box` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_box` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_generateIdentifier` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_getParent` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_move` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_rotate_no_offset` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_rotate_offset` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_setChanged` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_skew_no_offset_one_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_skew_no_offset_two_values` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_skew_offset_one_value` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_skew_offset_two_values` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_transform` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_translate` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_deprecated_update` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_component_removed_setParent` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated__generateIdentifer` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated__generateIdentiferforPoint` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated__get_box` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_box` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_generateIdentifer` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_generateIdentiferForPoint` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_getParent` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_move` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_reverseContour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_rotate_no_offset` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_rotate_offset` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_scale_center` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_scale_no_center` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_setChanged` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_skew_no_offset_one_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_skew_no_offset_two_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_skew_offset_one_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_skew_offset_two_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_transform` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_translate` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_deprecated_update` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_contour_removed_setParent` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_feature_removed_round` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_feature_removed_setParent` | pass | pass | font=live-font | capability: font.features.text.split | capability: font.features.text.split |
| `fontParts.test.test_deprecated.TestDeprecated.test_features_deprecated_getParent` | pass | pass | font=live-font | capability: font.features.text.split | capability: font.features.text.split |
| `fontParts.test.test_deprecated.TestDeprecated.test_features_deprecated_setChanged` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_features_deprecated_update` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_deprecated__fileName` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_deprecated__get_selection` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_deprecated__set_selection` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RGlyph.<lambda>: No native primitive implements this FontParts operation | font=live-font | capability: RGlyph.<lambda> | capability: RGlyph.<lambda> |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_deprecated_fileName` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_deprecated_getGlyph` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_deprecated_getWidth` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_deprecated_selection_get` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_deprecated_selection_set` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RGlyph.<lambda>: No native primitive implements this FontParts operation | font=live-font | capability: RGlyph.<lambda> | capability: RGlyph.<lambda> |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_deprecated_setChanged` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_deprecated_update` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_removed_compileGlyph` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_removed_generateGlyph` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_removed_getGlyphNameToFileNameFunc` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_removed_getParent` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_font_removed_setParent` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated__get_box` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_box` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_getAnchors` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_getComponents` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_getParent` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_get_mark` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_mark` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_move` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_readGlyphToString` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_rotate_no_offset` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_rotate_offset` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_scale_center` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_scale_no_center` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_setChanged` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_set_mark` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_skew_no_offset_one_value` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_skew_no_offset_two_values` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_skew_offset_one_value` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_skew_offset_two_values` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_transform` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_translate` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_update` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_deprecated_writeGlyphToString` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_removed_center` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_removed_clearHGuides` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_removed_clearVGuides` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_glyph_removed_setParent` | pass | pass | font=live-font, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_deprecated.TestDeprecated.test_groups_deprecated_getParent` | pass | pass | font=live-font | capability: groups.nativeMapping | capability: groups.nativeMapping |
| `fontParts.test.test_deprecated.TestDeprecated.test_groups_deprecated_setChanged` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_groups_removed_setParent` | pass | pass | font=live-font, groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated__generateIdentifer` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_generateIdentifer` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_getParent_font` | pass | pass | font=live-font, guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_getParent_glyph` | pass | pass | glyph=fontshell-parity, guideline=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_move` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_rotate_no_offset` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_rotate_offset` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_scale_center` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_scale_no_center` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_setChanged` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_skew_no_offset_one_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_skew_no_offset_two_values` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_skew_offset_one_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_skew_offset_two_values` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_transform` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_translate` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_deprecated_update` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_guideline_removed_setParent` | pass | pass | font=live-font, guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_deprecated.TestDeprecated.test_image_deprecated_getParent` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.image |
| `fontParts.test.test_deprecated.TestDeprecated.test_image_deprecated_setChanged` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_deprecated.TestDeprecated.test_image_deprecated_update` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_deprecated.TestDeprecated.test_image_removed_setParent` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.image |
| `fontParts.test.test_deprecated.TestDeprecated.test_info_deprecated_getParent` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_info_deprecated_setChanged` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_info_removed_setParent` | pass | pass | font=live-font, info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_add` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_combine` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_eliminate` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_explodeClasses` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_getAverage` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_getExtremes` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_getLeft` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_getParent` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_getRight` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_implodeClasses` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_importAFM` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_minimize` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_occurrenceCount` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_setChanged` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_setParent` | pass | pass | font=live-font, kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_kerning_removed_swapNames` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_deprecated.TestDeprecated.test_layer_deprecated_getParent` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_deprecated.TestDeprecated.test_layer_deprecated_setChanged` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_layer_deprecated_update` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_layer_removed_setParent` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_deprecated.TestDeprecated.test_lib_deprecated_getParent_font` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_lib_deprecated_getParent_glyph` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_lib_deprecated_setChanged` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_lib_removed_setParent_font` | pass | pass | font=live-font, lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_lib_removed_setParent_glyph` | pass | pass | glyph=fontshell-parity, lib=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated__generateIdentifier` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_generateIdentifier` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_move` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_rotate_no_offset` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_rotate_offset` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_scale_center` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_scale_no_center` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_setChanged` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_skew_no_offset_one_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_skew_no_offset_two_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_skew_offset_one_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_skew_offset_two_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_transform` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_translate` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_deprecated_update` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_getParent` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_removed_select` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_point_removed_setParent` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_getParent` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_move` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_rotate_no_offset` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_rotate_offset` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_scale_center` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_scale_no_center` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_setChanged` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_skew_no_offset_one_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_skew_no_offset_two_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_skew_offset_one_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_skew_offset_two_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_transform` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_translate` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_deprecated_update` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_removed_insertPoint` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_removed_removePoint` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_deprecated.TestDeprecated.test_segment_removed_setParent` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_features.TestFeatures.test_get_parent_font` | pass | pass | font=live-font | capability: font.features.text.split | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_get_parent_noFont` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_hash` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_object_equal_self` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_object_equal_self_variable_assignment` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_object_not_equal_other` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_object_not_equal_self_variable_assignment` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_reprContents` | pass | pass | font=live-font | capability: font.features.text.split | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_reprContents_noFont` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_set_parent_font` | pass | pass | features=fontshell-parity, font=live-font | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_set_parent_font_exists` | pass | pass | font=live-font | capability: font.features.text.split | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_set_parent_font_none` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_text_get` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_text_invalid_set` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_text_set_none` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_features.TestFeatures.test_text_valid_set` | pass | pass | features=fontshell-parity | capability: testing.nativeOrphan.features | capability: font.features.text.split |
| `fontParts.test.test_font.TestFont.test_appendGuideline_overrides` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_appendGuideline_position` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_appendGuideline_raises` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_appendGuideline_valid_object` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font, guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_font.TestFont.test_characterMapping` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_clearGuideline` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_close` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_copy` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: font.copy: Use explicit UFO export/import; implicit native document creation is refused | font=live-font | capability: font.copy | capability: font.copy |
| `fontParts.test.test_font.TestFont.test_copyData_source_layer_not_in_layerOrder` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RLayer.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_dublicateLayer` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: layer.copy: Use explicit detached UFO staging; orphan native layers have no owner | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_duplicateLayer_layerName_missing` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_duplicateLayer_newLayerName_exists` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_flatKerning` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_font.TestFont.test_font_tempLib` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_generateFormatToExtension` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_generate_format_none` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_generate_invalid_environmentOption` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_generate_invalid_format_type` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_generate_path_is_dir` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_generate_path_is_dir_and_self_path_none` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_generate_path_none` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_generate_path_none_and_self_path_none` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_generate_valid_environmentOption` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_getLayer_unknown` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_getReverseComponentMapping` | pass | pass | font=live-font | capability: glyph.geometry | capability: glyph.geometry |
| `fontParts.test.test_font.TestFont.test_glyphOrder` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_hash_different_object` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_hash_different_object_variable_assignment` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_hash_is_hasbable` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_hash_same_object` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_hash_same_object_variable_assignment` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_insertGlyph` | pass | pass | font=live-font, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.image |
| `fontParts.test.test_font.TestFont.test_insertLayer` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RLayer.<lambda>: Fontport has no native primitive for this operation | font=live-font, layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: layer.rename |
| `fontParts.test.test_font.TestFont.test_insertLayer_name_exists` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RLayer.<lambda>: Fontport has no native primitive for this operation | font=live-font, layer=fontshell-parity | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_insertLayer_name_none` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RLayer.<lambda>: Fontport has no native primitive for this operation | font=live-font, layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: layer.rename |
| `fontParts.test.test_font.TestFont.test_interpolate` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: font.interpolate: Native master replacement must not delete layers before interpolation preflight | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_font.TestFont.test_interpolate_asymmetric_layers` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: font.interpolate: Native master replacement must not delete layers before interpolation preflight | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_interpolate_global_guidelines` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_interpolate_invalid_types` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_interpolate_missing_default_layer` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: font.interpolate: Native master replacement must not delete layers before interpolation preflight | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_isCompatible_guideline_counts_differ` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_isCompatible_guidelines_differ` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_isCompatible_layer_counts_differ` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_isCompatible_layer_fatal_only` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: glyph.delete.master | capability: glyph.delete.master |
| `fontParts.test.test_font.TestFont.test_isCompatible_layer_warning_only` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: glyph.delete.master | capability: glyph.delete.master |
| `fontParts.test.test_font.TestFont.test_isCompatible_layers_differ` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: layer.rename | capability: layer.rename |
| `fontParts.test.test_font.TestFont.test_len_initial` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_len_two_layers` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_newGlyph_rename` | pass | pass | font=live-font | capability: glyph.rename | capability: glyph.rename |
| `fontParts.test.test_font.TestFont.test_newLayer_colored_layer_exists` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RLayer.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_newLayer_layer_exists` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_object_equal_self` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_object_equal_self_variable_assignment` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_object_not_equal_other` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_object_not_equal_other_variable_assignment` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_removeGuideline_index` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_removeGuideline_index_out_of_range` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_removeLayer` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_reprContents` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_reprContents_path` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_round` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_font.TestFont.test_save` | pass | pass | font=live-font | capability: font.save.format | capability: font.save.format |
| `fontParts.test.test_font.TestFont.test_save_and_close` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_save_fileStructure` | pass | pass | font=live-font | capability: font.save.format | capability: font.save.format |
| `fontParts.test.test_font.TestFont.test_save_formatVersion` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: font.save.ufoVersion: ufoLib2 writes UFO 3 only | font=live-font | capability: font.save.ufoOptions | capability: font.save.ufoOptions |
| `fontParts.test.test_font.TestFont.test_save_path_none` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_selectedGlyphNames_default` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_selectedGlyphNames_setEmptyList` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_selectedGlyphNames_setFilledList` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_selectedGlyphNames_setSubObject` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_selectedGlyphs_default` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_selectedGlyphs_setEmptyList` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_selectedGlyphs_setFilledList` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_selectedGlyphs_setSubObject` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_selectedGuidelines_default` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_selectedGuidelines_setEmptyList` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_selectedGuidelines_setFilledList` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_selectedGuidelines_setSubObject` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_font.TestFont.test_selectedLayerNames_default` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_selectedLayerNames_setEmptyList` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_selectedLayerNames_setFilledList` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_selectedLayerNames_setSubObject` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_selectedLayer_default` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_selectedLayer_setEmptyList` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_selectedLayer_setFilledList` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_selectedLayer_setSubObject` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_selected_false` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_selected_true` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_font.TestFont.test_swapLayerNames` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_font.TestFont.test_swapLayerNames_names_missing` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_glyph.TestGlyph.test_addImage` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: glyph.image: Native image storage is unavailable | font=live-font | capability: glyph.image | capability: glyph.image |
| `fontParts.test.test_glyph.TestGlyph.test_appendAnchor_valid_object` | pass | pass | anchor=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_appendComponent_invalid_circularReference` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_appendComponent_invalid_object_circularReference` | pass | pass | component=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_appendComponent_valid_object` | pass | pass | component=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_appendComponent_valid_object_baseGlyph` | pass | pass | component=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_appendComponent_valid_object_conflictingIdentifier` | pass | pass | component=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_appendComponent_valid_object_offset` | pass | pass | component=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_appendComponent_valid_object_scale` | pass | pass | component=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_appendContour_offset_valid` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_appendGlyph` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_appendGuideline_valid_object` | pass | pass | glyph=fontshell-parity, guideline=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_autoContourOrder_bboxsurface` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_autoContourOrder_distantCenter` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_autoContourOrder_fuzzycenter` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_autoContourOrder_points` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_autoContourOrder_segments` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_bottomMargin_get` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_bottomMargin_set_invalid_none` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_bottomMargin_set_invalid_string` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_bottomMargin_set_valid_float` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_bottomMargin_set_valid_negative` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_bottomMargin_set_valid_positive` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_bottomMargin_set_valid_zero` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_clear` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_clearAnchors` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_clearComponents` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_clearContours` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_clearGuidelines` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_getLayer_invalid` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_glyph.TestGlyph.test_getLayer_valid` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_glyph.TestGlyph.test_getLayer_valid_not_found` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_glyph.TestGlyph.test_get_bottomMargin_not_set` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_get_bounds` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_get_contour_invalid` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_get_font` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_glyph.TestGlyph.test_get_font_orphan_glyph` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_glyph.TestGlyph.test_get_layer` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_glyph.TestGlyph.test_get_layer_orphan_glyph` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_glyph.TestGlyph.test_get_layers` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_glyph.TestGlyph.test_get_layers_orphan_glyph` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_get_leftMargin_not_set` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_get_name` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_get_name_not_set` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_glyph.TestGlyph.test_get_rightMargin_not_set` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_get_topMargin_not_set` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_get_unicode` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_get_unicode_not_set` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_get_unicodes` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_get_unicodes_not_set` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_hash_object_other` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_hash_object_other_variable_assignment` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_hash_object_self` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_hash_object_self_variable_assignment` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_height_get` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_height_set_invalid_none` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_height_set_invalid_string` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_height_set_valid_float` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_height_set_valid_negative` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_height_set_valid_positive` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_height_set_valid_zero` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_insertContour_offset_valid` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_interpolate_glyphWidth_with_rounding` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_interpolate_glyphWidth_without_rounding` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_isCompatible_anchors` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_isCompatible_anchors_disjoint` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_isCompatible_anchors_intersecting` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_isCompatible_anchors_order` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_isCompatible_components` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_glyph.TestGlyph.test_isCompatible_components_disjoint` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_glyph.TestGlyph.test_isCompatible_components_disjoint_equal_size` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_glyph.TestGlyph.test_isCompatible_components_intersecting` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_glyph.TestGlyph.test_isCompatible_components_order` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: components.unresolvedBase |
| `fontParts.test.test_glyph.TestGlyph.test_isEmpty_false_component` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_isEmpty_false_outlines` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_isEmpty_true_clear` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_is_hashable` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_leftMargin_get` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_leftMargin_set_invalid_none` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_leftMargin_set_invalid_string` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_leftMargin_set_valid_float` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_leftMargin_set_valid_negative` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_leftMargin_set_valid_positive` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_leftMargin_set_valid_zero` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_moveBy_only_contours` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_newLayer_invalid` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_glyph.TestGlyph.test_newLayer_valid` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_glyph.TestGlyph.test_newLayer_valid_already_exists` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_glyph.TestGlyph.test_not_selected_false` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_object_equal_self` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_object_equal_variable_assignment` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_object_not_equal_other` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_object_not_equal_other_name_same` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_object_not_equal_variable_assignment` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_removeAnchor_invalid` | pass | pass | anchor=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_removeAnchor_valid` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_removeComponent_invalid` | pass | pass | component=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_removeComponent_valid` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_removeContour_invalid` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_removeContour_valid` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_removeGuideline_invalid` | pass | pass | glyph=fontshell-parity, guideline=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_removeGuideline_valid` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_removeLayer_invalid` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: glyph.removeLayer.retainedHandle: Use font.getLayer(name).removeGlyph(name); native handles become stale after removal rather than orphaned | font=live-font | capability: glyph.removeLayer.retainedHandle | capability: glyph.removeLayer.retainedHandle |
| `fontParts.test.test_glyph.TestGlyph.test_removeLayer_valid_not_found_type_string` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: glyph.removeLayer.retainedHandle: Use font.getLayer(name).removeGlyph(name); native handles become stale after removal rather than orphaned | font=live-font | capability: glyph.removeLayer.retainedHandle | capability: glyph.removeLayer.retainedHandle |
| `fontParts.test.test_glyph.TestGlyph.test_removeLayer_valid_type_glyph_layer` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: glyph.removeLayer.retainedHandle: Use font.getLayer(name).removeGlyph(name); native handles become stale after removal rather than orphaned | font=live-font | capability: glyph.removeLayer.retainedHandle | capability: glyph.removeLayer.retainedHandle |
| `fontParts.test.test_glyph.TestGlyph.test_removeLayer_valid_type_string` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: glyph.removeLayer.retainedHandle: Use font.getLayer(name).removeGlyph(name); native handles become stale after removal rather than orphaned | font=live-font | capability: glyph.removeLayer.retainedHandle | capability: glyph.removeLayer.retainedHandle |
| `fontParts.test.test_glyph.TestGlyph.test_removeOverlap` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_rightMargin_get` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_rightMargin_set_invalid_none` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_rightMargin_set_invalid_string` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_rightMargin_set_valid_float` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_rightMargin_set_valid_negative` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_rightMargin_set_valid_positive` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_rightMargin_set_valid_zero` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedAnchors_default` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedAnchors_setEmptyList` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedAnchors_setFilledList` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedAnchors_setSubObject` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedComponents_default` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedComponents_setEmptyList` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedComponents_setFilledList` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedComponents_setSubObject` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedContours_default` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedContours_setEmptyList` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedContours_setFilledList` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedContours_setSubObject` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedGuidelines_default` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedGuidelines_setEmptyList` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedGuidelines_setFilledList` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selectedGuidelines_setSubObject` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_selected_true` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_set_name_invalid` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_glyph.TestGlyph.test_set_name_valid` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_set_unicode_invalid` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_set_unicode_valid` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_set_unicode_value` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_set_unicode_value_none` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_set_unicodes_duplicates` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_set_unicodes_invalid` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_set_unicodes_valid` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_glyph.TestGlyph.test_topMargin_get` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_topMargin_set_invalid_none` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_topMargin_set_invalid_string` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_topMargin_set_valid_float` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_topMargin_set_valid_negative` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_topMargin_set_valid_positive` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_topMargin_set_valid_zero` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_width_get` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_width_set_invalid_none` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_width_set_invalid_string` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_width_set_valid_float` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_width_set_valid_negative` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_width_set_valid_positive` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_glyph.TestGlyph.test_width_set_valid_zero` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.rename |
| `fontParts.test.test_groups.TestGroups.test_asDict` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_contains_found` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_contains_not_found` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_find_found` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_find_invalid_key` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_find_not_found` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_get_fallback_default` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_get_found` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_get_not_found` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_get_parent_font` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_groups.TestGroups.test_get_parent_font_none` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_groups.TestGroups.test_get_side1KerningGroups` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_get_side2KerningGroups` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_hash` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_iter` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_iter_remove` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_len_add` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_len_clear` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_len_initial` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_len_subtract` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_object_equal_self` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_object_equal_self_variable_assignment` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_object_not_equal_other` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_object_not_equal_other_variable_assignment` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_remove` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_remove_nonexistant_group` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_remove_twice` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_reprContents` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_groups.TestGroups.test_reprContents_noFont` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_groups.TestGroups.test_set_parent_differentFont` | pass | pass | font=live-font, groups=fontshell-parity | capability: testing.nativeOrphan.groups | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_groups.TestGroups.test_set_parent_font` | pass | pass | font=live-font, groups=fontshell-parity | capability: testing.nativeOrphan.groups | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_groups.TestGroups.test_set_parent_font_none` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_groups.TestGroups.test_side1KerningGroups` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_side2KerningGroups` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_groups.TestGroups.test_values` | pass | pass | groups=fontshell-parity | capability: testing.nativeOrphan.groups | capability: groups.nativeMapping |
| `fontParts.test.test_guideline.TestGuideline.test_angle_get_fontGuideline` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_guideline.TestGuideline.test_angle_get_generic` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_get_glyphGuideline` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_invalid_negative_edge` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_invalid_positive_edge` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_invalid_string` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_None` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_negative` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_negative_edge` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_negative_float` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_none_x0_y0` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_none_x0_y1` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_none_x1_y0` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_none_x1_y1` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_positive` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_positive_edge` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_positive_float` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_zero_fontGuideline` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_zero_generic` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_angle_set_valid_zero_glyphGuideline` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_guideline.TestGuideline.test_color_get_none` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_color_set_invalid_int` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_color_set_invalid_over_max` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_color_set_invalid_string` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_color_set_invalid_too_few` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_color_set_invalid_uner_min` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_color_set_none` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_color_set_valid_decimal` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_color_set_valid_max` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_color_set_valid_min` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_copy_generated_identifier_different` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_copy_same_angle` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_copy_same_color` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_copy_same_identifier` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_copy_same_name` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_copy_same_x` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_copy_same_y` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_copy_seperate_objects` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_get_index` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_get_index_noParent` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_get_parent_font` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_guideline.TestGuideline.test_get_parent_glyph` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_get_parent_layer` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_get_parent_noFont` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_get_parent_noGlyph` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_get_parent_noLayer` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_hash_object_other` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_hash_object_other_variable_assignment` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_hash_object_self` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_hash_object_self_variable_assignment` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_identifier_cannot_set` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_identifier_consistency` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_identifier_force_set` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_identifier_generated_type` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_identifier_get_none` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_is_hashable` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_moveBy_invalid_all_strings_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_moveBy_invalid_int_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_moveBy_invalid_one_string_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_moveBy_valid` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_name_get_none` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_name_set_invalid` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_name_set_none` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_name_set_valid` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_not_selected_false` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_object_equal_self` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_object_equal_self_variable_assignment` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_object_not_equal_other` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_object_not_equal_other_variable_assignment` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_reprContents` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_reprContents_Layer` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_guideline.TestGuideline.test_reprContents_noGlyph` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_rotateBy_invalid_string_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_rotateBy_invalid_too_large_value_negative` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_rotateBy_invalid_too_large_value_positive` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_rotateBy_valid_no_origin` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_rotateBy_valid_origin` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_round_angle` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_round_at_half` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_round_close_to` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_scaleBy_invalid_one_string_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_scaleBy_invalid_tuple_too_many_values` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_scaleBy_invalid_two_string_values` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_scaleBy_valid_one_value_no_origin` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_scaleBy_valid_two_values_no_origin` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_scaleBy_valid_two_values_origin` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_selected_true` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_set_index_negative` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_set_index_noParent` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_set_index_positive` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_set_parent_font_font_exists` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_guideline.TestGuideline.test_set_parent_font_glyph_exists` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_guideline.TestGuideline.test_set_parent_font_none` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_set_parent_glyph` | pass | pass | glyph=fontshell-parity, guideline=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_set_parent_glyph_exists` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_set_parent_glyph_font_exists` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_guideline.TestGuideline.test_set_parent_glyph_none` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_skewBy_valid_no_origin_one_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_skewBy_valid_no_origin_two_values` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_skewBy_valid_origin_one_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_skewBy_valid_origin_two_values` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_transformBy_invalid_all_string_values` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_transformBy_invalid_int_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_transformBy_invalid_one_string_value` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_transformBy_valid_no_origin` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_transformBy_valid_origin` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_x_get_fontGuideline` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_guideline.TestGuideline.test_x_get_generic` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_x_get_glyphGuideline` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_guideline.TestGuideline.test_x_set_invalid_string` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_x_set_valid_None` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_x_set_valid_negative` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_x_set_valid_negative_float` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_x_set_valid_positive` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_x_set_valid_positive_float` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_x_set_valid_zero_fontGuideline` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_guideline.TestGuideline.test_x_set_valid_zero_generic` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_x_set_valid_zero_glyphGuideline` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_guideline.TestGuideline.test_y_get_fontGuideline` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_guideline.TestGuideline.test_y_get_generic` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_y_get_glyphGuideline` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_guideline.TestGuideline.test_y_set_invalid_string` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_y_set_valid_None` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_y_set_valid_negative` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_y_set_valid_negative_float` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_y_set_valid_positive` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_y_set_valid_positive_float` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_y_set_valid_zero_fontGuideline` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_guideline.TestGuideline.test_y_set_valid_zero_generic` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_guideline.TestGuideline.test_y_set_valid_zero_glyphGuideline` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_image.TestImage.test_bool_data` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_bool_data_len_zero` | upstream-skip | upstream-skip: Cannot set zero data | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_bool_no_data` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_data_get` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_data_get_direct` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_data_set_invalid` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_data_set_invalid_png` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_data_set_valid` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_data_set_valid_direct` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_get_color_no_parent` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_get_color_no_parent_none` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_get_color_parent` | pass | pass | font=live-font | capability: glyph.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_get_color_parent_none` | pass | pass | font=live-font | capability: glyph.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_get_offset` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_get_offset_set` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_get_parent_font` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_image.TestImage.test_get_parent_glyph` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_image.TestImage.test_get_parent_layer` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_image.TestImage.test_get_parent_noFont` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_image.TestImage.test_get_parent_noGlyph` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_get_parent_noLayer` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_image.TestImage.test_get_scale` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_get_scale_set` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_get_transformation` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_hash_object_other` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_hash_object_other_variable_assignment` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_hash_object_self` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_hash_object_self_variable_assignment` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_is_hashable` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_object_equal_self` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_object_equal_self_variable_assignment` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_object_not_equal_other` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_object_not_equal_other_variable_assignment` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_reprContents` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_reprContents_glyph` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_image.TestImage.test_reprContents_glyph_color` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_image.TestImage.test_reprContents_noColor` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_round` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_round_half` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_selected_false` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_selected_true` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_color` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_color_invalid` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_offset` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_offset_invalid_none` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_offset_invalid_string` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_parent_glyph` | pass | pass | glyph=fontshell-parity, image=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_parent_glyph_exists` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_image.TestImage.test_set_parent_glyph_none` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_scale` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_scale_invalid_none` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_scale_invalid_string` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_tranformation` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_set_tranformation_invalid` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_transformBy_valid_no_origin` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_image.TestImage.test_transformBy_valid_origin` | pass | pass | image=fontshell-parity | capability: testing.nativeOrphan.image | capability: glyph.image |
| `fontParts.test.test_info.TestInfo.test_copy` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | capability: info.postscriptBlueValues |
| `fontParts.test.test_info.TestInfo.test_get_unitsPerEm` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_info.TestInfo.test_hash` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_info.TestInfo.test_interpolate_unitsPerEm_with_rounding` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_info.TestInfo.test_interpolate_unitsPerEm_without_rounding` | pass | UnsupportedCapability: fontlab_fontport.errors.UnsupportedCapability: RFont.<lambda>: Fontport has no native primitive for this operation | font=live-font | capability: RFont.<lambda> | capability: RFont.<lambda> |
| `fontParts.test.test_info.TestInfo.test_object_equal_self` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_info.TestInfo.test_object_equal_self_variable_assignment` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_info.TestInfo.test_object_not_equal_other` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_info.TestInfo.test_object_not_equal_other_variable_assignment` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_info.TestInfo.test_round_unitsPerEm` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | capability: info.unitsPerEm.fractional |
| `fontParts.test.test_info.TestInfo.test_set_invalid_unitsPerEm_negative` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_info.TestInfo.test_set_invalid_unitsPerEm_string` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_info.TestInfo.test_set_valid_unitsPerEm_float` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | capability: info.unitsPerEm.fractional |
| `fontParts.test.test_info.TestInfo.test_set_valid_unitsPerEm_int` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | pass |
| `fontParts.test.test_info.TestInfo.test_update` | pass | pass | info=fontshell-parity | capability: testing.nativeOrphan.info | capability: info.openTypeNamePreferredFamilyName |
| `fontParts.test.test_kerning.TestKerning.test_asDict_returnIntegers_empty` | pass | pass | kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | pass |
| `fontParts.test.test_kerning.TestKerning.test_asDict_returnIntegers_false` | pass | pass | kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_asDict_returnIntegers_true` | pass | pass | kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_contains_glyph_glyph` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_contains_glyph_group` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_contains_group_group` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_contains_missing_glyph_glyph` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_del` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_find_glyph_glyph` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_find_glyph_glyph_none` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_find_glyph_group` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_find_group_glyph` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_find_group_group` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_get_fallback_default` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_get_fallback_default_user` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_get_font` | pass | pass | font=live-font, kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | pass |
| `fontParts.test.test_kerning.TestKerning.test_get_font_orphan_font` | pass | pass | kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_kerning.TestKerning.test_get_glyph_glyph` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_get_glyph_group` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_get_group_glyph` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_get_group_group` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_hash` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_interpolate_incompatible_contents_supressError` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_interpolate_incompatible_keys_raise` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_interpolate_incompatible_keys_supressError` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_interpolate_maxKerning_invalid_type` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_interpolate_minKerning_invalid_type` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_interpolate_with_rounding` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_interpolate_without_rounding` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_len_clear` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_len_initial` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_object_equal_self` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_object_equal_self_variable_assignment` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_object_not_equal_other` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_object_not_equal_other_variable_assignment` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_remove` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_reprContents` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_reprContents_no_font` | pass | pass | kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_round_large_multiple` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_round_multiple_1` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_round_multiple_2` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_round_multiple_invalid_type` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_round_multiple_zero` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_round_negative_values` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_scaleBy_factor` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_scaleBy_float` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_scaleBy_int` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_set_font` | pass | pass | font=live-font, kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_kerning.TestKerning.test_set_font_different_value` | pass | pass | font=live-font, kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | pass |
| `fontParts.test.test_kerning.TestKerning.test_set_font_same_value` | pass | pass | font=live-font, kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | pass |
| `fontParts.test.test_kerning.TestKerning.test_set_font_value_none` | pass | pass | kerning=fontshell-parity | capability: testing.nativeOrphan.kerning | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_kerning.TestKerning.test_set_glyph_glyph` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_set_glyph_group` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_set_group_glyph` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_kerning.TestKerning.test_set_group_group` | pass | pass | font=live-font | capability: kerning.danglingNames | capability: kerning.danglingNames |
| `fontParts.test.test_layer.TestLayer.test_get_glyph_in_font` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_get_glyph_not_in_font` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_hash_object_other` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_hash_object_other_variable_assignment` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_hash_object_self` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_hash_object_self_variable_assignment` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_is_hashable` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_len` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_object_equal_self` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_object_equal_self_variable_assignment` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_object_not_equal_other` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_object_not_equal_self_variable_assignment` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_selectedGlyphNames_default` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_selectedGlyphNames_setEmptyList` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_selectedGlyphNames_setFilledList` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_selectedGlyphNames_setSubObject` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_selectedGlyphs_default` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_selectedGlyphs_setEmptyList` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_selectedGlyphs_setFilledList` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_selectedGlyphs_setSubObject` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_selected_false` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_selected_true` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_layer.TestLayer.test_set_glyph` | pass | pass | glyph=fontshell-parity, layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: glyph.rename |
| `fontParts.test.test_layer.TestLayer.test_set_glyph_with_name_None` | pass | pass | glyph=fontshell-parity, layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: glyph.image |
| `fontParts.test.test_lib.TestLib.test_contains_found` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_contains_not_found` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_get_found` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_get_parent_font` | pass | pass | font=live-font, lib=fontshell-parity | capability: layer.create | capability: layer.create |
| `fontParts.test.test_lib.TestLib.test_get_parent_glyph` | pass | pass | glyph=fontshell-parity, lib=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_lib.TestLib.test_get_parent_noFont` | pass | pass | layer=fontshell-parity, lib=fontshell-parity | capability: testing.nativeOrphan.layer | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_lib.TestLib.test_get_parent_noGlyph` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_lib.TestLib.test_hash` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_keys` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_len_clear` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_len_initial` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_object_equal_self` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_object_equal_self_variable_assignment` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_object_not_equal_other` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_object_not_equal_other_variable_assignment` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_reprContents` | pass | pass | lib=fontshell-parity | capability: testing.nativeOrphan.lib | pass |
| `fontParts.test.test_lib.TestLib.test_set_parent_glyph` | pass | pass | glyph=fontshell-parity, lib=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeAnchorName_notLongEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeAnchorName_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeAnchorName_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeAnchor_notAnchor` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeAnchor_valid` | pass | pass | anchor=fontshell-parity | capability: testing.nativeOrphan.anchor | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeArea_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeArea_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeArea_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeArea_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeArea_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeArea_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBPointType_CORNER` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBPointType_Corner` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBPointType_OFFCURVE` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBPointType_OffCurve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBPointType_corner` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBPointType_curve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBPointType_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBPointType_unknown` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBPoint_notBPoint` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBPoint_valid` | pass | pass | bPoint=fontshell-parity | capability: testing.nativeOrphan.bPoint | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoolean_0` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoolean_1` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoolean_10` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoolean_false` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoolean_string` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoolean_true` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_float` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_int` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_invalidMember` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_list` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_notEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_notListOrTuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_tooMany` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_tuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_xMaxLessThanXMin` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_xMinSameAsXMax` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_yMaxLessThanYMin` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeBoundingBox_yMinSameAsYMax` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_color` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_floats` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_ints` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_invalidMember` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_list` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_notEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_notTupleOrList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_tooLarge` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_tooMany` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_tooSmall` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeColor_tuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_listNegativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_listNegativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_listPositiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_listPositiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_listZero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_notEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_notNumberNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_notTupleOrList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_numberNotNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_tooMany` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_tupleNegativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_tupleNegativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_tuplePositiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_tuplePositiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponentScale_tupleZero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponent_notComponent` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeComponent_valid` | pass | pass | component=fontshell-parity | capability: testing.nativeOrphan.component | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeContour_notContour` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeContour_valid` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeCoordinateTuple_list` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeCoordinateTuple_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeCoordinateTuple_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeCoordinateTuple_notEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeCoordinateTuple_notNumberNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeCoordinateTuple_numberNotNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeCoordinateTuple_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeCoordinateTuple_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeCoordinateTuple_tooMany` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeCoordinateTuple_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeDefaultLayerName_notInFont` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeDefaultLayerName_notValidLayerName` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeDefaultLayerName_valid` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeFeatureText_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeFeatureText_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeFileFormatVersion_float` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeFileFormatVersion_int` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeFileFormatVersion_invalid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeFilePath_emptyString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeFilePath_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeFilePath_pathlib_fillPath` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeFilePath_pathlib_simplePath` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeFilePath_string` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphBottomMargin_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphBottomMargin_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphBottomMargin_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphBottomMargin_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphBottomMargin_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphBottomMargin_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphFormatVersion_float1` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphFormatVersion_float2` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphFormatVersion_float3` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphFormatVersion_int1` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphFormatVersion_int2` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphFormatVersion_int3` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphFormatVersion_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphHeight_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphHeight_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphHeight_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphHeight_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphHeight_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphHeight_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphLeftMargin_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphLeftMargin_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphLeftMargin_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphLeftMargin_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphLeftMargin_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphLeftMargin_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphName_notLongEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphName_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphName_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphNote_emptyString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphNote_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphNote_string` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphOrder_duplicate` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphOrder_invalidMember` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphOrder_notList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphOrder_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphOrder_validTuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphRightMargin_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphRightMargin_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphRightMargin_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphRightMargin_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphRightMargin_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphRightMargin_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphTopMargin_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphTopMargin_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphTopMargin_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphTopMargin_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphTopMargin_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphTopMargin_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicode_invalidFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicode_invalidRangeMaximum` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicode_invalidRangeMinimum` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicode_invalidString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicode_validHex` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicode_validInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicode_validRangeMaximum` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicode_validRangeMinimum` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicodes_invalidDuplicateMembers` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicodes_invalidMember` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicodes_notTupleOrList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicodes_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyphUnicodes_validTuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyph_notGlyph` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGlyph_valid` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGroupKey_notLongEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGroupKey_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGroupKey_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGroupValue_invalidMember` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGroupValue_notList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGroupValue_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGroupValue_validEmpty` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGroupValue_validTuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGuidelineName_notLongEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGuidelineName_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGuidelineName_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGuideline_notGuideline` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeGuideline_valid` | pass | pass | guideline=fontshell-parity | capability: testing.nativeOrphan.guideline | capability: glyph.guidelines |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIdentifier_none` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIdentifier_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIdentifier_stringAfterMaximumCharacter` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIdentifier_stringBeforeMinimumCharacter` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIdentifier_stringMaximumCharacter` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIdentifier_stringMaximumLength` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIdentifier_stringMinimumCharacter` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIdentifier_stringMinimumLength` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIdentifier_stringTooLong` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIdentifier_stringTooShort` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIndex_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIndex_notInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIndex_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeIndex_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_listNegativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_listNegativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_listPositiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_listPositiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_listZero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_notEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_notNumberNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_notTupleOrList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_numberNotNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_tooMany` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_tupleNegativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_tupleNegativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_tuplePositiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_tuplePositiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_tupleZero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeInterpolationFactor_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningKey_invalidSide1Group` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningKey_invalidSide2Group` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningKey_memberNotLongEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningKey_memberNotString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningKey_notEnoughMembers` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningKey_notTuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningKey_tooManyMembers` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningKey_validGlyphs` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningKey_validGroups` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningKey_validList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningValue_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningValue_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningValue_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningValue_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningValue_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeKerningValue_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayerName_notLongEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayerName_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayerName_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayerOrder_duplicate` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayerOrder_invalidMember` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayerOrder_notInFont` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayerOrder_notList` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayerOrder_valid` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayerOrder_validTuple` | pass | pass | font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayer_notLayer` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLayer_valid` | pass | pass | layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibKey_emptyString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibKey_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibKey_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_invalidDictKey` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_invalidDictValue` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_invalidListMember` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_invalidNone` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_invalidTupleMember` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_validDict` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_validFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_validInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_validList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_validString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeLibValue_validTuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointName_notLongEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointName_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointName_valid` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_CURVE` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_Curve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_LINE` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_Line` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_MOVE` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_Move` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_OFFCURVE` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_OffCurve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_QOFFCURVE` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_QOffCurve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_curve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_line` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_move` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_offcurve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_qcurve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePointType_unknown` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePoint_notContour` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePoint_notPoint` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizePoint_valid` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeRotationAngle_lessThanMaximum` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeRotationAngle_maximum` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeRotationAngle_minimum` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeRotationAngle_moreThanMaximum` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeRotationAngle_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeRotationAngle_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeRotationAngle_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeRotationAngle_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeRotationAngle_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeRotationAngle_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_LINE` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_Line` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_MOVE` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_Move` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_OFFCURVE` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_OffCurve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_QOFFCURVE` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_QOffCurve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_curve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_line` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_move` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_notString` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_qcurve` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegmentType_unknown` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeSegment_valid` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationMatrix_invalidMember` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationMatrix_list` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationMatrix_negativeFloats` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationMatrix_negativeInts` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationMatrix_notEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationMatrix_notTupleOrList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationMatrix_positiveFloats` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationMatrix_positiveInts` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationMatrix_tooMany` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationMatrix_tuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_listNegativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_listNegativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_listPositiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_listPositiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_listZero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_notEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_notNumberNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_notTupleOrList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_numberNotNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_tooMany` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_tupleNegativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_tupleNegativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_tuplePositiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_tuplePositiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationOffset_tupleZero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_float` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_int` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_list` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_listNegativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_listNegativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_listPositiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_listPositiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_listZero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_notEnough` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_notNumberNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_notTupleOrList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_numberNotNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_tooMany` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_tuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_tupleNegativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_tupleNegativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_tuplePositiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_tuplePositiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationScale_tupleZero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_float` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_int` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_list` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_negativeFloats` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_negativeInts` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_notNumberNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_notTupleOrList` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_numberNotNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_positiveFloats` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_positiveInts` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_tooFew` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_tooHigh` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_tooLow` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_tooMany` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_tuple` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeTransformationSkewAngle_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeVisualRounding_float` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeVisualRounding_half` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeVisualRounding_half_even` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeVisualRounding_int` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeVisualRounding_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeX_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeX_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeX_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeX_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeX_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeX_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeY_negativeFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeY_negativeInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeY_notNumber` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeY_positiveFloat` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeY_positiveInt` | pass | pass | none | pass | pass |
| `fontParts.test.test_normalizers.TestNormalizers.test_normalizeY_zero` | pass | pass | none | pass | pass |
| `fontParts.test.test_point.TestPoint.test_copyData_different_identifier` | pass | pass | contour=fontshell-parity, point=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_point.TestPoint.test_copyData_name` | pass | pass | contour=fontshell-parity, point=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copyData_smooth` | pass | pass | contour=fontshell-parity, point=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copyData_type` | pass | pass | contour=fontshell-parity, point=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copyData_x` | pass | pass | contour=fontshell-parity, point=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copyData_y` | pass | pass | contour=fontshell-parity, point=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copy_different_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copy_different_identifier` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_point.TestPoint.test_copy_generated_identifier_different` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_point.TestPoint.test_copy_none_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copy_same_identifier_None` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_point.TestPoint.test_copy_same_name` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copy_same_smooth` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copy_same_type` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copy_same_x` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copy_same_y` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_copy_seperate_objects` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_getIdentifer_consistency` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_point.TestPoint.test_getIdentifer_no_contour` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | capability: identifiers |
| `fontParts.test.test_point.TestPoint.test_get_index` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_get_index_noParentContour` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_point.TestPoint.test_get_name_hasName` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_get_name_noName` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_get_parent_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_get_parent_font` | pass | pass | contour=fontshell-parity, font=live-font | capability: layer.create | capability: layer.create |
| `fontParts.test.test_point.TestPoint.test_get_parent_font_noContour` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_point.TestPoint.test_get_parent_glyph` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_point.TestPoint.test_get_parent_glyph_noContour` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_point.TestPoint.test_get_parent_layer` | pass | pass | contour=fontshell-parity, layer=fontshell-parity | capability: testing.nativeOrphan.layer | pass |
| `fontParts.test.test_point.TestPoint.test_get_parent_layer_noContour` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_point.TestPoint.test_get_parent_noContour` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_point.TestPoint.test_get_parent_noFont` | pass | pass | contour=fontshell-parity, layer=fontshell-parity | capability: testing.nativeOrphan.layer | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_point.TestPoint.test_get_parent_noGlyph` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_point.TestPoint.test_get_parent_noLayer` | pass | pass | contour=fontshell-parity, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_point.TestPoint.test_get_parent_segment` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | pass |
| `fontParts.test.test_point.TestPoint.test_get_smooth` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_get_type` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_get_x` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_get_y` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_hash_object_other` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_hash_object_other_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_hash_object_self` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_hash_object_self_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_identifier_cannot_set` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_identifier_consistency` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_point.TestPoint.test_identifier_generated_type` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | capability: identifiers |
| `fontParts.test.test_point.TestPoint.test_identifier_get_none` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_is_hashable` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_moveBy_invalid_all_strings_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_moveBy_invalid_int_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_moveBy_invalid_one_string_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_moveBy_valid` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_object_equal_self` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_object_equal_self_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_object_not_equal_other` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_object_not_equal_other_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_reprContents` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_reprContents_isSmooth` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_reprContents_noContour` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | pass |
| `fontParts.test.test_point.TestPoint.test_reprContents_withName` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_rotateBy_invalid_string_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_rotateBy_invalid_too_large_value_negative` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_rotateBy_invalid_too_large_value_positive` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_rotateBy_valid_no_origin` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_rotateBy_valid_origin` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_roundX` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | pass |
| `fontParts.test.test_point.TestPoint.test_roundY` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | pass |
| `fontParts.test.test_point.TestPoint.test_scaleBy_invalid_one_string_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_scaleBy_invalid_tuple_too_many_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_scaleBy_invalid_two_string_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_scaleBy_valid_one_value_no_origin` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_scaleBy_valid_two_values_no_origin` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_scaleBy_valid_two_values_origin` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_selected_false` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_selected_true` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_already_set_parent_contour` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_curve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_index` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_invalid_point_type_int` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_invalid_point_type_string` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_move` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_name_invalidType` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_name_valid_none` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_name_valid_str` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_offcurve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_parent_contour` | pass | pass | contour=fontshell-parity, point=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_point.TestPoint.test_set_parent_contour_none` | pass | pass | point=fontshell-parity | capability: testing.nativeOrphan.point | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_point.TestPoint.test_set_smooth_invalid` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_smooth_valid` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_wcurve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_x_invalidType` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_x_valid_float` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_x_valid_int` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_y_invalidType` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_y_valid_float` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_set_y_valid_int` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_skewBy_valid_no_origin_one_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_skewBy_valid_no_origin_two_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_skewBy_valid_origin_one_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_skewBy_valid_origin_two_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_transformBy_invalid_all_string_values` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_transformBy_invalid_int_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_transformBy_invalid_one_string_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_transformBy_valid_no_origin` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_point.TestPoint.test_transformBy_valid_origin` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_curve_pt_types` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_curve_pt_x_y` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_equal_invalid_type` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_get_contour` | pass | pass | contour=fontshell-parity, segment=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_get_contour_orphan_segment` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_get_font` | pass | pass | font=live-font, glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | capability: glyph.image |
| `fontParts.test.test_segment.TestSegment.test_get_font_orphan_segment` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_get_glyph` | pass | pass | glyph=fontshell-parity | capability: testing.nativeOrphan.glyph | pass |
| `fontParts.test.test_segment.TestSegment.test_get_glyph_orphan_segment` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_get_index` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_get_index_orphan_segment` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_get_layer` | pass | pass | glyph=fontshell-parity, layer=fontshell-parity | capability: testing.nativeOrphan.layer | capability: glyph.image |
| `fontParts.test.test_segment.TestSegment.test_get_layer_orphan_segment` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_get_onCurve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_get_onCurve_no_points` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_get_smooth` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_get_smooth_no_oncurve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_hash` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_isCompatible` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_isCompatible_inconvertible_types` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_iter` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_len` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_len_curve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_len_move` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_len_orphan_segment` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_len_qcurve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_object_equal_self` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_object_equal_self_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_object_not_equal_other` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_object_not_equal_other_variable_assignment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_offCurve_only_segment` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_oncuve_type_move` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_oncuve_x_y` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_qcurve_pt_types` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_qcurve_pt_x_y` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_reprContents` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_reprContents_no_index` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | pass |
| `fontParts.test.test_segment.TestSegment.test_round` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_selected_false` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_selected_true` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_set_conotur` | pass | pass | contour=fontshell-parity, segment=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_set_contour_value_none` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_set_contour_value_set` | pass | pass | contour=fontshell-parity, segment=fontshell-parity | capability: testing.nativeOrphan.contour | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_set_curve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_set_invalid_segment_type_int` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_set_invalid_segment_type_string` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_set_move` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_set_qcurve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_set_smooth` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_set_smooth_no_oncurve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_set_type_no_oncurve` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_set_type_orphan_segment` | pass | pass | segment=fontshell-parity | capability: testing.nativeOrphan.segment | harness exclusion: testing.nativeAttached.parents |
| `fontParts.test.test_segment.TestSegment.test_set_type_same_value` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_segment.TestSegment.test_type_get` | pass | pass | contour=fontshell-parity | capability: testing.nativeOrphan.contour | pass |
| `fontParts.test.test_world.TestFontList.test_getFontsByFamilyName` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_world.TestFontList.test_getFontsByFamilyNameStyleName` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_world.TestFontList.test_getFontsByStyleName` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_world.TestFontList.test_sortBy_familyName` | pass | pass | font=live-font | capability: info.unset | capability: info.unset |
| `fontParts.test.test_world.TestFontList.test_sortBy_fontInfoAttribute_xHeight` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_world.TestFontList.test_sortBy_isItalic_italicAngle` | pass | pass | font=live-font | capability: info.styleMapStyleName | capability: info.styleMapStyleName |
| `fontParts.test.test_world.TestFontList.test_sortBy_isItalic_styleMapStyleName` | pass | pass | font=live-font | capability: info.styleMapStyleName | capability: info.styleMapStyleName |
| `fontParts.test.test_world.TestFontList.test_sortBy_isMonospace_glyphs` | pass | pass | font=live-font | capability: info.postscriptIsFixedPitch | capability: info.postscriptIsFixedPitch |
| `fontParts.test.test_world.TestFontList.test_sortBy_isMonospace_postscriptIsFixedPitch` | pass | pass | font=live-font | capability: info.postscriptIsFixedPitch | capability: info.postscriptIsFixedPitch |
| `fontParts.test.test_world.TestFontList.test_sortBy_isProportional_glyphs` | pass | pass | font=live-font | capability: info.postscriptIsFixedPitch | capability: info.postscriptIsFixedPitch |
| `fontParts.test.test_world.TestFontList.test_sortBy_isProportional_postscriptIsFixedPitch` | pass | pass | font=live-font | capability: info.postscriptIsFixedPitch | capability: info.postscriptIsFixedPitch |
| `fontParts.test.test_world.TestFontList.test_sortBy_isRoman_italicAngle` | pass | pass | font=live-font | capability: info.styleMapStyleName | capability: info.styleMapStyleName |
| `fontParts.test.test_world.TestFontList.test_sortBy_isRoman_styleMapStyleName` | pass | pass | font=live-font | capability: info.styleMapStyleName | capability: info.styleMapStyleName |
| `fontParts.test.test_world.TestFontList.test_sortBy_sortValueFunction` | pass | pass | font=live-font | pass | pass |
| `fontParts.test.test_world.TestFontList.test_sortBy_styleName` | pass | pass | font=live-font | capability: info.unset | capability: info.unset |
| `fontParts.test.test_world.TestFontList.test_sortBy_weightValue` | pass | pass | font=live-font | capability: info.unset | capability: info.unset |
| `fontParts.test.test_world.TestFontList.test_sortBy_widthValue` | pass | pass | font=live-font | capability: info.unset | capability: info.unset |
| `fontParts.test.test_world.TestFontOpen.test_font_open` | pass | pass | font=live-font | capability: font.save.format | capability: font.save.format |
| `fontParts.test.test_world.TestFontShell_RFont.test_fontshell_RFont_empty` | pass | pass | none | pass | pass |
| `fontParts.test.test_world.TestOpenFonts.test_font_open` | pass | pass | font=live-font | capability: font.save.format | capability: font.save.format |
