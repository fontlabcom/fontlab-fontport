---
this_file: src_docs/md/guides/NATIVE-BOUNDARIES.md
---

# Native boundaries for B05/B06 and live handles

The App can import `NATIVE_CAPABILITIES` and `STRUCTURED_ROUTES` from
`fontlab_fontport.capabilities`, or ask `NativeFontBackend.capabilities()` for
a detached snapshot. A false capability is an explicit contract, not a probe
that mutates a document. `glyph.externalChangeNotifications` is false: native
edits/Undo/Redo do not notify defcon automatically. Show “Reload required”,
call `font.refresh()` and reacquire glyph/layer handles. Adapter-originated
accepted edits still mark defcon dirty and invalidate component representations.

`StaleObjectError` identifies closed documents and invalidated/removed bindings.
Public cached glyph/child/info/group/kerning/feature/lib reads check the owner;
backend IDs are reacquired rather than retaining FontLab native pointers. A
private `.naked()` defcon object deliberately obtained before closure is outside
the guarded FontParts API. Do not keep/use native wrappers after closure.

| Boundary | Current contract / C4 reproducer |
|---|---|
| Exact one info Undo row | D18 default `require_single_undo=False` keeps info editable with the verified extra no-op row. Opt-in True refuses changing batches before checkpoint/write. C4 single-undo phases test the refusal; structured phases explicitly opt into legacy history to probe real setters |
| Optional absent metric | None raises `UnsupportedCapability('info.<field>.absent', ...)`, before any assignment/checkpoint; no zero is written. Concrete native master doubles do not encode absence. C4 unset-metric phases |
| Unicode native classes | Changing mappings containing Unicode class names raise `groups.unicodeNames` before native construction/write/history. Existing identical mappings remain no-ops. C4 unicode-class phases |
| Divergent both-sided classes | One native class has one membership array. Divergent public.kern1/kern2 projections of that same native group raise `groups.divergentBothSides` during planning, before writes/checkpoints. C4 both-sided phases require a real KernBothSide fixture; a missing prerequisite is a failed native acceptance check |
| Legacy native group flags / VFJ | `require_persistence=True` is opt-in; the default False preserves v1.0.0 editing/save. Font-global groups not in FeaClassGroupMode cause changing group mappings and VFJ saves to refuse before writes/history. Ordinary feature/current-master groups remain editable. Explicit False opts into the old route. C4 creates an owned legacy-mode fixture, verifies group-write/save refusal and file absence, then removes it before structured setter checks. Original FontLab flag loss still needs an upstream issue |
| Fractional native kerning | Any changing operation involving current/requested fractional kerning raises `kerning.fractionalHistory` before writes/history. An identical fractional snapshot remains a no-op. C4 fractional-kerning phases |
| Fractional native anchors | `_stage_source` refuses as `glyph.anchor.precision` before import/native staging or target writes. A rejected live edit restores the accepted defcon model. C4 glyph/fractional-anchor phases |
| Non-ASCII glyph names | `glyph.name.unicodeVfj` refuses before native create/rename/geometry writes. No speculative encoding conversion. C4 glyph/unicode-name phases |

D18 preserves the **v1.0.0 default editing contract**. Info edits and saves work;
strict history/persistence checks are opt-in (`require_single_undo=True` on
info.apply, `require_persistence=True` on backend group/save operations).
Untouched legacy groups and Unicode glyph names do not block ordinary saves.
Fontport refuses unsafe new glyph names, fractional anchors/kerning and other
unroundtrippable edits before writing; these never become save-time surprises.
It does not certify that FontLab preserves every foreign baseline field.
The extra-checkpoint and legacy-VFJ defects remain unresolved host behavior.
C4 owns filing/linking the fl
issues with the actual build, original failing receipts and minimal reproducer.

## Structured storage correction after C4 T9

The fg::Style setters are not evidence of native persistence. C4 on 9.0.9783
measured lost Panose/weight/width/name-record writes after Undo/VFJ reopening.
The master-backed routes now used by Fontport match Font Info:

| Field | Bound property / source | Persisted storage / source |
|---|---|---|
| openTypeOS2Panose | flPackage.panose string; Proteus/pygate/pyflpackage.cpp:1512–1516 | keyPackageMaster._panose, flpackage.cpp:17199–17220; master writer :5875 |
| openTypeOS2WeightClass | flPackage.weight_value; pyflpackage.cpp:949 | keyPackageMaster._weight_value, flpackage.cpp:17350–17354; writer :5853 |
| openTypeOS2WidthClass | flPackage.width_value; pyflpackage.cpp:951 | keyPackageMaster._width_value, flpackage.cpp:17356–17360; writer :5854 |
| openTypeNameRecords | Changing writes refuse info.openTypeNameRecords.persistence | info setter mutates regenerated fg::Style names (pyflpackage.cpp:2031–2078). Font Info writes localizedNames via setLocalizedNames (workspace2/fontinfo_data.cpp:520; flpackage.cpp:16806–16836), absent from the Python bindings/stubs. MCP set_font_info's global whitelist (common/mcp/mcptools_fonts.cpp:469–565) has no localized/name-record route. |
| postscriptStemSnapH/V | Existing info setters, pyflpackage.cpp:3197,3237 | Existing native stem routes; C4 T9 did not report their Undo/VFJ failure |

The model source paths above are under Proteus/common/model/. Font Info itself
loads master values at fontinfo_data.cpp:391–392 and Panose at :402, then stores
the same properties at :586–596. Panose's empty native string reads as absent
(None), not invented zeros. Weight/width getter rounding follows fg::round.

All validation and name-record refusal precede checkpoints or writes, including
mixed batches. Master-backed writes retain package/mastersContainer pre/post
notifications. C4 must re-run the phased read/edit/Undo/Redo/VFJ checks; source
verification and mocked checkpoints do not prove the new route natively.
The catalogue marks the derived name-record getter as bound but write=None,
write_supported=False, rather than advertising the nonpersistent setter.

## Named native limits and lib keys

Dangling native kerning glyph/group references refuse kerning.danglingNames;
MCP's own group creation resolves actual flGlyph objects before its command
(common/mcp/mcptools_metrics_kerning.cpp:709–715). Plain feature classes retain
their existing mapping policy. No phantom glyphs are created.
Unresolved/cyclic components refuse components.unresolvedBase, identifiers
refuse identifiers, and unsetting concrete non-metric info refuses info.unset.
Metric absence retains the more specific info.<field>.absent name.

Native QVariant tuples are recursively exposed as UFO lists. The known host
key com.fontlab.kerningClassesInMainMaster is hidden from public font.lib keys,
kept unchanged through edits/clear, and cannot be assigned through that view
(lib.reservedKey). Other foreign lib entries remain visible and keep the
existing unchanged-leaf preservation contract.

## Master scope and unfinished geometry (Round 13)

Panose, OS/2 weight and OS/2 width writes affect the **key master only**, not
every master. Their package properties delegate to keyPackageMaster (source
locations in the table above); batch callers must not infer all-master edits.

Invalidation, refresh, save and staged edits refuse `glyph.incompleteContours`
while provisional point sequences remain. Closing emits a RuntimeWarning with
that capability name before discarding provisional edits and closing the owned
document with save=False. This permits fixture cleanup without silently losing
editing state. Complete or remove provisional contours before invalidating.

Non-integral UPM refuses `info.unitsPerEm.fractional` before writes. Integral
floats and integer subclasses used by UFO OS/2 weight/width exports are accepted;
bools are not numeric metrics.

## Round-14 history and explicit master scope

`glyph.exactSingleUndo` is false: pre/post notifications add a no-op checkpoint
in addition to the restoring edit. Working shapes are cloned after the baseline
notification to keep stored geometry untouched. The first Undo must restore
contours.

`capabilities()` exposes each Panose/weight/width/stem-snap route with
`bound: "key-master"`; STRUCTURED_ROUTES reports the same scope. No per-master
write argument is advertised. Invalid per-side native class membership refuses
`groups.multiMembership` before mutation/history.

Round-15 read comparisons exclude only root MCP `lastModified`, named
`fontlab.lastModified`: it is an edit/save timestamp, not a reversible font value.
Raw receipts retain it; nested lib values with that name remain significant.
Glyph creation history is counted on the package, subsequent glyph edits on
the glyph graph. Undo/Redo/reopen payload and geometry comparisons remain gates.
