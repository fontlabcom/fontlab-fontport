---
this_file: src_docs/md/guides/INTEGRATION.md
---

# Fontport integration examples and limits

These additions have host-free tests. The native handoff is
[NATIVE-MANIFEST.json](https://github.com/fontlabcom/fontlab-fontport/blob/bbe74e286b8281ae22b383cf42755d9d084c8aae/verification/issue-105/NATIVE-MANIFEST.json), with an
[owned GetGo probe](https://github.com/fontlabcom/fontlab-fontport/blob/bbe74e286b8281ae22b383cf42755d9d084c8aae/tests/native_drivers/fontport_owned.py). Run the host-side CLI through `fl-native.sh --mutating`. It creates a unique
ignored `.local/native-issue105/` run directory, warms imports separately, and
uses one native operation per call with a four-second timing budget. No native receipt is claimed for these additions.

## Explicit FontParts environment

The examples require installed `fontlab-fly>=1.3.0` and their canonical providers.

```python
from fly.fp.world import FontWorld, register

environment = FontWorld()                 # native imports happen on calls
borrowed = environment.CurrentFont()      # None when no documents exist
with register(environment):
    from fontParts import world
    assert world.CurrentFont() is borrowed
    fonts = world.AllFonts()
# The previous dispatcher is restored, including on an exception.
```

`environment.OpenFont(absolute_owned_copy)` and `NewFont(...)` return owned
handles. Their `close()` discards the owned native document; borrowed close only
invalidates that binding. Registration closes no documents. `world.RFont()`
creates a native document while registered; `world.RFont(existing_fontport_font)`
returns the same handle. Native open/new require `showInterface=True`.

Call `environment.refresh()` after edits or Undo made outside Fontport. This
invalidates loaded layer/glyph snapshots and removes externally closed fonts
from the handle cache. Native callbacks are not subscribed automatically, and
native `CurrentGlyph`/selection dispatch raises `NotImplementedError` explicitly.
Native save currently writes a copy; it does not clear FontLab's dirty state or
change its source filename. Unexpected native assignment failures are not a
transactional rollback facility.

## Feature editing and font data

```python
from fontParts.fontshell import RFont
from fly.fp.fontdata import FeatureEdit, stage_lib

font = RFont()                            # actual upstream detached environment
edit = FeatureEdit(font.features)
edit.text = "# Ω\nfeature liga { sub f i by fi; } liga;\n"
assert edit.dirty
edit.revert()                            # typing has not changed the font
edit.text = "# Ω\n"
edit.apply()                             # explicit public FontParts text setter
font.lib.update(stage_lib({"nested": {"bytes": b"\x00", "values": [1, True]}}))
```

Fontport's live `features` and `lib` are real `BaseFeatures`/`BaseLib` objects.
The feature wrapper preserves exact text and distinguishes `None` from `""`;
`FeatureEdit` also works with actual upstream fontshell objects. Feature text
is data, never Python, and no compile action is exposed. Native FontGate has
separate stored prefix/tag blocks, read through the VFJ-canonical fontpr serializer.
Use `font.features.get_blocks()` and `set_blocks({"prefix": text, "features": [(tag, code)]})`.
Only arbitrary replacement-text splitting is unsupported; see [the API contract](NATIVE-FEATURES.md).

Actual FontParts UFO output preserves CRLF bytes on write; current fontTools
UFOReader normalizes CRLF to LF on reopen. A regression records that upstream
boundary, rather than claiming byte-exact reloaded feature text.

`stage_lib` accepts supported XML plist strings, integers, finite reals, booleans,
arrays, dictionaries, binary data and naive UTC dates with whole-second
precision. It validates serialization without parsing the XML back, preserving CR/CRLF.
It canonicalizes arrays to lists and rejects lossy date precision,
nonfinite values, invalid nested keys and unserializable values before dispatch.
Reads are detached: reassign a nested value to persist changes. `lib.update`
validates changed values as a batch; `lib.apply` replaces the mapping while
leaving unchanged foreign leaves opaque, including inside nested mappings and
arrays. Foreign JSON null/control text/large integers survive valid sibling
edits. Array leaves match by index; moving a foreign leaf counts as a new write.

Native font lib uses `flPackage.packageLib` and currently permits JSON-compatible
values only, for changed leaves, with new numbers within the exact JSON integer range. Unchanged
foreign values are deep-copied without plist/JSON normalization. Binary/date data
is refused before native history/mutation. This application-level map is not
proof of automatic `fgFont.lib` or native UFO-export synchronization.

`info.apply` additionally stages descriptive name/legal fields, localized
`openTypeNameRecords`, OS/2 weight/width/Panose and PostScript horizontal/vertical
stem lists. It uses fontTools' UFO3 validators plus native numeric bounds, with
detached structured values. These native routes need individual persistence and
Undo proof. The advertised native `postscriptBlueValues` setter is unimplemented
and remains unavailable. Optional metric clearing remains unavailable too.

## Vanilla controls moved to Glyport

Fontport holds only FontParts and UFO code. It has no Vanilla session and no
UI shim for windows, controls or dialogs. `VanillaSession` moved to
`fontlab_glyport.ui.session` (issue 122). Install the separately distributed
`fontlab-glyport` wheel for it; Fontport does not depend on Glyport.

```python
# old (removed): from fontlab_fontport.vanilla import VanillaSession
from fly.gp.ui.session import VanillaSession
```

`fontlab_fontport.vanilla` has been deleted (issue 201; its one-release
tombstone expired). Session behaviour, window ownership and teardown are
documented with Glyport. The FontParts-bound editors (font info, groups,
kerning, transform, batch, glyph sequence) now live in `fontlabapp.fontui`;
install App’s `fontport` extra. The old `fontlab_fontport.ui` package only
raises migration errors and goes in the next release. Active-font feature I/O
also lives in `fontlabapp.fontui.feature_blocks`; the deprecated Fontport path
forwards lazily and needs Fontport’s optional `fontlab` extra.

## Detached B09 operations

```python
from pathlib import Path
from ufoLib2 import Font
from fly.fp.operations import BatchRunner, Recipe, transform_font
from fly.fp.designspace import Designspace

root = Path("/absolute/owned-output")
recipe = Recipe(matrix=(1.2, 0, 0, 1, 10, 0), intensity=50)
with Font.open(root / "owned-source.ufo") as source:
    preview = transform_font(source, recipe)
preview.save(root / "new-output.ufo", overwrite=False)
recipe.save("new-settings.json")            # exclusive creation
assert Recipe.load("new-settings.json") == recipe
inspectable_python = recipe.script()         # returned text; never auto-executed
for result in BatchRunner().run([(root / "owned-source.ufo", root / "batch-output.ufo")], recipe):
    print(result.ok, result.error)
model = Designspace.open("owned.designspace")
coordinates = model.defaults()
instance = model.instance(coordinates)       # always labelled as an instance
```

These are affine transforms with explicit enable/intensity/reset semantics,
using fontTools pens. They transform outlines/anchors/guides/images/components
without modifying source objects. Whole-font component transforms are conjugated
to avoid scaling transformed bases twice. Width/height are scalar advance-vector
projections; font metrics and kerning are retained. No stem/topology-preserving
or interpolation method is simulated. Singular matrices are refused.

`Designspace` reads actual source/instance locations from fontTools descriptors,
maps design to user coordinates, reports missing source files and validates
axis endpoints/defaults. `Designspace.from_native(backend)` snapshots native
axes/master/instance locations without switching the current source. Echopy sidecars and native flAxis bindings confirm its native map is design→user;
the adapter reverses it for fontTools. GetGo comparison is still required. Discrete axes,
anisotropic locations and multi-axis maps are explicitly unavailable.

`BatchRunner` eagerly preflights and reserves at call time (before returning an
iterator), accepts at most 256 UFO source/destination pairs, and forbids
overwrite/case-insensitive duplicate targets, yields per-attempt results, resets running state
on failure/cancel/iterator close and can call progress/cancellation callbacks.
Exhaust or close its iterator; close works before the first next call too. A large
single-file transform is synchronous and belongs outside FontLab's UI thread.
The native acceptance driver processes a small owned UFO inside FontLab, one
attempt per RPC with progress/native document polls between calls and a <4 s
budget. That tests cooperative between-file responsiveness for this fixture;
large-font preemption and UI scheduling remain Fontlabapp acceptance work.
Partial output may remain after a write failure; a batch
is not an atomic transaction. `export_ufo_subset`/`compile_ttf` remain selected
geometry export/external compilation, not complete native font conversion.

Fontport needs no Glyport. The manifest command may still add import roots via `--extra-source`.
Append `--dry-run` to the Python driver invocation to check source origins
without connecting or copying fixtures (do not invoke the mutating wrapper for
a host-free dry run). Fontport package trees are purged in FontLab and imported
`__file__` paths asserted against preflight results. Native phases let the normal
event loop process deferred deletion between RPCs. After **every mutating run**,
including failure, restart the test FontLab before the next suite. The shared
`fl-native.sh` manages sessions but does not perform this post-run restart.

## API sources

Implementation uses the official [FontParts environment contracts](https://fontparts.robotools.dev/en/latest/environments/objects/index.html),
[fontTools transform pens](https://fonttools.readthedocs.io/en/latest/pens/transformPen.html),
[designspace descriptors](https://fonttools.readthedocs.io/en/latest/designspaceLib/python.html),
[UFO validators](https://fonttools.readthedocs.io/en/latest/ufoLib/index.html) and
[ufoLib2 copying/reference APIs](https://ufolib2.readthedocs.io/en/latest/reference.html),
plus the installed upstream source and native binding declarations. Runtime
proof and source inspection are recorded separately in the manifest/work log.

Host-facing open, save, subset export, compilation and batch APIs refuse relative
paths instead of consulting FontLab's process cwd.
