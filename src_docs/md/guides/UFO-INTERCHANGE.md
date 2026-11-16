---
this_file: src_docs/md/guides/UFO-INTERCHANGE.md
---

# Whole-font UFO interchange

`ExportSession(backend).steps()` reads every named layer/glyph, then supported
info, groups, kerning, lib and feature text using real ufoLib2. Exhaust steps
before `save(absolute_ufo_path)`, which refuses overwrite. Inside FontLab use
the round10 native controller: it transfers one GLIF/metadata unit at a time and
saves the assembled UFO externally. `.losses` records native exclusions and
invalid native info values. The borrowed source is never edited or closed.

`ImportSession(source, native=True).preflight_steps()` first detaches/checks
one glyph per step, then metadata. Only after exhaustion can `.begin(factory)`
allocate a new native backend and return `(font, steps)`. Advance once per RPC;
close the owned font in finally. Outside the fixed host deadline, the convenience
`with import_native(ufo) as (font, steps):` exhausts preflight and closes on exit.
`import_ufo(ufo, backend_factory)` offers the same protocol for a caller-supplied
backend. The host-free UFOBackend is explicitly a test/storage backend.

New-native import explicitly opts into the legacy info-history/group routes
because this is a newly constructed owned document, not an editor batch. This
does not promise one Undo row or restore legacy flags omitted by UFO conversion.
Ordinary editor setters retain v1.0.0 defaults under D18; strict checks are opt-in.

Import creates component bases before assigning outlines/components. Preflight
refuses missing/cyclic bases, unsupported layer topology, Unicode native names,
fractional native anchors/kerning, unsupported anchor metadata/guidelines/images,
non-JSON native lib values and feature code that cannot survive native history.
No native destination exists when these checks refuse. Unexpected apply failures
are not a native transaction; the owned partially constructed font is discarded.

| Field | Host-free UFO round trip | Native mapping / loss |
|---|---|---|
| Layer names/default layer, all glyph names | Preserved | Export reads every layer. Import currently accepts only one layer and maps it to the new native default master. Multiple native layers/masters refuse before allocation |
| Contours, on/off curves, smooth flags | Preserved | Read through native shape transforms; plain unhinted shape writes only. Original shape partition/style/transform identity is not retained |
| Components and affine matrices | Preserved | Exported by base name. New native import creates bases first. Existing component replacement/removal in a live document refuses |
| Width, height, unicodes, note, glyph lib | Preserved | Native Unicode/note/lib are glyph-global, not independent UFO-layer metadata; widths/outlines/anchors are layer-specific. Non-ASCII glyph names refuse native writes |
| Anchors | Fractional positions/names preserved | Integral named positions supported; fractions, color, identifier and unnamed anchors refuse native import/write |
| Guidelines (glyph/font) | Glyph guidelines preserved in UFOBackend tests | Native layer/font guidelines are not exported. Native writes/import refuse guidelines. Export therefore lists this loss |
| Glyph/layer colors, identifiers, image data, image transforms | Not a tested whole-backend field | Native read adapter does not expose them; images and unsupported anchor metadata refuse import. Native image bytes are not exported |
| Kerning, explicit zeros, groups | Preserved | Current-key-master mapping only; other masters' pairs/classes, key glyphs and legacy flags are not represented. Fractions and divergent native both-sided memberships refuse writes |
| Features | Exact text retained | VFJ-canonical prefix/ordered blocks exported. Reserved lib key `org.fontlab.fontport.featureBlocks` retains exact native boundaries for import; a pre-existing collision refuses. This extra interchange entry is removed on import |
| OT class definitions | Groups retained independently | Class declarations are not injected into feature text, avoiding duplication. Use recipes.parse_features(..., classes=groups) for feaLib. UFO consumers requiring inline classes must combine them deliberately |
| Info | INFO_FIELDS retained | Exact list: info.INFO_FIELDS. Other UFO info attributes are outside the native adapter. Invalid native UFO values (e.g. empty Panose/width class 0) become absent and get individual loss entries |
| Optional absent info | Retained with UFOBackend | Native concrete double metrics cannot be unset; absent UFO metrics remain native defaults on import, not a promise of absence. No invented zero is written |
| Font lib | Nested plist values retained | Foreign JSON null/non-plist values refuse export serialization; native imports accept the documented JSON subset only. Unknown lib leaves are never silently filtered |
| UPM and coordinate scale | Values retained | No rescaling is implied by changing UPM |
| Axes, mappings, instances, interpolation state | Not a UFO-font field | `designspace_io.export_designspace` (issue 201) writes a `.designspace` and one UFO per master from the native layers and `Designspace.from_native`. Kerning is read per master (`flPackage.kerning(master)`) and written to each master UFO; rules, labels, per-master groups/info/features and brace layers are not read (`designspace_io.LOSSES`). Import: `native_import.import_designspace` (below) |
| Hints/TT programs, masks, native metrics links, zones, shape sharing/styles/builders, audit/UI/selection/history/export state | Not represented | Native-only data has no implementation here. Live edits preserve untouched native state; a UFO/new-native round trip cannot reconstruct it |
| Glyph/layer order beyond backend enumeration | Not a native-order restoration contract | Layer enumeration and glyph order are exposed; native reordering is unavailable |

## Native UFO and designspace routes (task 17, measured on FontLab 9)

Owned copies, closed with `save=False`; probe in the workspace scratch.

- MCP `save_font` writes only `.vfj`, `.vfc` or `.vfjp`; it has no UFO route.
- `fgFont.save("x.ufo")` is lossy, which is why `ExportSession` stays the UFO
  and designspace exporter: it writes the current master only (a 3-master font
  gave one `glyphs` layer), no `kerning.plist` (64 source pairs), and no anchors
  (0 glifs, 348 anchor blocks in the source VFJ). It does write fontinfo,
  groups, lib, features and metainfo.
- `open_font("x.ufo")` returns ok and imports the glyphs as one master.
- `open_font("x.designspace")` with one Weight axis and two sources imported both
  masters and the axis as one font. Kerning and anchor import were not checked
  (the probe UFOs had none).

`import_ufo_native(path)` and `import_designspace(path)` call the same
`NativeApplication.open_font` (`fontpr.call("open_font", path=...)`) and return an
owned `NativeFontBackend`. They refuse a wrong suffix, a missing file or a
relative path, and convert nothing, so no Fontport loss list applies.

These are a bounded conversion and an explicit inventory, not a lossless native
font archive. Use VFJ for that purpose. Full multilevel native guidelines, native
layer creation and variable metadata interchange remain open; C4 should return
reopened UFO/VFJ comparisons for the Latin, variable and non-Latin fixtures.

Round-15 native comparison contract: absent/None and empty notes are equivalent
(`fontlab.note.empty`), and numeric values compare numerically without tolerance
(`fontlab.numericValue`). Raw values and point-pen digests are retained in native
receipts. Real metric, outline, nonempty note, lib and anchor differences fail.
