---
this_file: src_docs/md/guides/LIVE-PEN-RECIPES.md
---

# Pens on live FontParts objects

Use real upstream classes; Fontport never registers substitute namespaces.
Caller owns the destination font and precreates output glyphs in a separate
phase. `font.edit_glyph` stages an operation on an ordinary detached fontshell
glyph, commits once and invalidates loaded handles. Fetch a fresh glyph after
commit. Exceptions inside the context write nothing.

The examples require installed `fontlab-fly>=1.3.0` and their canonical providers.

```python
from fly.fp.recipes import digest, bounds, flatten, transform_into

live_digest = digest(font['A'])   # actual fontPens.DigestPointPen
rectangle = bounds(font['A'], font)  # actual fontTools.BoundsPen
flatten(font, 'A', 'fontport_flat')  # actual fontPens.FlattenPen
transform_into(font, 'A', 'fontport_shifted', (1, 0, 0, 1, 25, 0))
```

Flatten decomposes components through the live glyph set, then writes the whole
path once. Native Undo-row behavior remains a C4 gate; one backend commit alone
does not prove one native Undo row. Fractional anchor/hint/shared-shape limits
still apply to live destinations. Use an owned empty destination, not a hinted
GetGo source glyph.

MarginPen and TransformPointPen use the same real RGlyph interfaces:

```python
from fontPens.marginPen import MarginPen
from fontPens.transformPointPen import TransformPointPen

pen = MarginPen(font, 200, isHorizontal=False)
font['A'].draw(pen)
margins_at_200 = pen.getMargins()
with font.edit_glyph('fontport_shifted', undo_name='Shifted point-pen path') as target:
    target.clearContours()
    font['A'].drawPoints(TransformPointPen(target.getPointPen(), (1, 0, 0, 1, 25, 0)))
```

`Designspace.from_native(font._backend)` snapshots native axis/user maps, master
design locations and instances using fontTools.designspaceLib. It does not
create interpolated native instances. Native map keys are design coordinates;
the adapter reverses them to fontTools' (user, design) pairs.

`parse_features(font.features.text, font.keys(), classes=dict(font.groups))`
uses feaLib with native OT classes supplied separately; features.text excludes
panel classes intentionally. Includes are not followed automatically. Parse
errors retain locations and need comparison with fonts FontLab actually
compiles; syntax acceptance is not a native compile action.

C4 `--suite pens` warms imports, then reads/tests one native glyph at a time,
records raw digests and native/bounds rectangles, snapshots axes/masters and
parses features. Flatten edit, Undo and Redo are separate calls with full
expected/observed payload receipts. Repeat against static and variable GetGo
copies and return any slow phase or mismatch as a ticket.

Round-12 correction: `bounds()` keeps the actual curve extrema from BoundsPen.
FontLab's native boundingBox includes off-curve controls. Use
`control_bounds(glyph, font)` (ControlBoundsPen) for the native comparison; the
native receipt keeps both boxes. No y-axis inversion is inferred or hidden.

A live native contour may be built one point at a time. Empty contours allocate
no native geometry; incomplete controls or other temporarily invalid point
sequences stay in the Python model until a valid path exists. Native data is
unchanged during that interval. Saving an unfinished path raises
`glyph.incompleteContours`; finish/correct/remove it first. Standalone pens
still reject malformed paths. Identifiers refuse as `identifiers` before native
writes. The attached upstream generator supplies an empty contour, matching the
upstream factory, rather than inserting a triangle into every contour fixture.

Round-13 flattening puts fontTools RoundingPen between FlattenPen and the
destination pen. Each sampled coordinate rounds to the nearest integer using
fontTools otRound (half-way ties towards positive infinity). The rounding error
is at most 0.5 units per axis per sample; FlattenPen's curve approximation error
is separate. The native driver builds its expected digest through the same
rounding pen before comparing readback, Undo and Redo.

Round-14 history correction: a staged commit uses copy-on-write native shapes
after the baseline notification. The native pre/post protocol has an extra no-op
row, exposed as glyph.exactSingleUndo=False. The first Undo must restore actual
MCP contour/point records. One backend commit does not
mean one visible Undo row.
