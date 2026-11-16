---
this_file: src_docs/md/guides/NATIVE-FEATURES.md
---

# Native feature storage (FontLab 9)

Fontport reads VFJ-canonical feature text and writes explicit ordered blocks.
The Round-4 claim that no lossless native route existed was wrong: it missed
`fontpr.get_font_info`, which uses the VFJ writer, and the equivalence of the
bound fragment setters to FontLab's VFJ loader. This document supersedes that
claim. Native timing, first Undo/Redo and saved-artifact proof remain required.

```python
blocks = font.features.get_blocks()
# {"prefix": "...", "features": [("kern", "feature kern {...} kern;\n"), ...]}
tag, code = blocks["features"][0]
blocks["features"][0] = (tag, code + "\n# edited code\n")
font.features.set_blocks(blocks, undo_name="Edit feature")
assert font.features.text == blocks["prefix"] + "".join(code for tag, code in blocks["features"])
```

NativeFontBackend exposes the same operations as `get_feature_blocks()` and
`set_feature_blocks()`. Reads are detached. Prefix and feature strings preserve
Unicode, CR/CRLF, whitespace and comments; feature order is explicit. OT panel
classes remain separate font groups and are not duplicated into the prefix.

## Exact read path

`fontpr.get_font_info(font_id=...)` returns the `openTypeFeatures` array, with an
optional first `{feature: prefix}` entry followed by ordered `{name, feature}`
entries. `blocks_from_info(info)` parses that snapshot; `features.text` joins
its prefix and feature strings. Missing `openTypeFeatures` means empty stored
text, including a binary-only font. Malformed/unrecognized records raise rather
than being silently dropped.

VFJ permits named empty records such as `{"name": "ccmp"}`: its loader defaults
an omitted `feature` to an empty QString and stores an empty named slot. The
text-block API omits these textless slots (including explicit empty strings),
and ignores entirely empty anonymous records just as the loader does. Raw
`read_info` snapshots and driver receipts retain every original array record.
Sixteen GetGo VFJs have these empty named slots. A no-op text write preserves
them; a changing write refuses that current baseline before mutation, naming
the empty tag: the whole-text Undo stream cannot reconstruct a tag with no
text. This is an explicit native history limitation, not an unknown-record error.

Do not use `fgOTLayout.get_prefix()` as this source: it requests synthesized
panel classes. Do not use `keys()/get_feature()` either: they can fall back to
binary decompilation when stored FEA text is absent. Fontport has no such fallback.
If embedded `fontpr` is unavailable, reading fails explicitly with RuntimeError.

## Exact structured write path

The entire `{prefix: str, features: [(tag, code), ...]}` batch is validated before
history or mutation. Tags require four printable ASCII bytes, unique names and
`aalt` first if present (native storage forces it to the front). Strings must be
UTF-8 encodable and NUL-free. Syntax is stored without compilation.

Changing native writes refuse prefixes that require language-system synthesis. The
native test is a literal `languagesystem ` substring (even in a comment), or an
initial nonblank/noncomment line starting with `include`. Its scan splits on LF
or lone CR, trimming only space/tab/LF: a CRLF blank line retains `\r` and stops
the scan, so an include after it does not suppress synthesis. LF blank lines
are skipped. Otherwise FontLab can
prepend a `#> languagesystem` block during metadata reads or save/reopen.
Its generated script/language pairs depend on font glyph Unicode values,
feature bodies and native build options; the pure structured API lacks that
context and does not guess. `stage_blocks` checks only split-back fidelity.
`write_blocks` stages first, reads the current snapshot, and returns immediately
for identical values. Only a changing staged value receives the synthesis
check, before history/mutation; the current Undo baseline never does.
Feature-less fonts with no feaTextStorage have no serializer injection, so their
identical empty writes succeed and an explicit language-system feature add is
allowed. Changing/clearing a nonempty font to an empty prefix still raises a
precise `ValueError`, because clear/set_prefix would allocate storage that can
synthesize text. Reads remain available for every snapshot.

Undo/Redo restores a concatenated FEA stream through FontLab's whole-text
splitter, not through the VFJ array loader. Consequently `stage_blocks` and
`set_blocks` simulate that splitter with the pure `split_history_text` function
in `native_feature_split.py`. The acceptance rule is exact: concatenate the
prefix and ordered codes, simulate history loading, and require exactly the
same prefix and `(tag, code)` pairs back. There is no raw-keyword prohibition.

The simulation works on UTF-8 byte offsets with the native destructive strtok
semantics and delimiter set. When the next non-delimiter character is `#`, the
entire comment line is one token; `feature` inside it never splits a block.
After a header the native algorithm seeks the first matching tag token before
looking for the next `feature` token. Thus normal `aalt` references such as
`feature sups;` before the closing tag are accepted. Like native code, this is
not a brace-aware grammar: a matching tag token earlier in a body can affect
where the next keyword search begins. The simulation also models duplicate-tag
retention, `aalt` placement, LF appending by FeaTextBlock and name-table extraction.

Leading comments/whitespace in a named code, a different declared tag, multiple
independent blocks in one pair, or a name table removed on history loading are
refused when they change the reconstructed model. `ValueError` identifies the
affected prefix/block and differing prefix, tag, code or block count before
history or mutation. A changing write checks the current Undo baseline too.
A tagless trailing `feature` is refused before native calls: the native loader
can read past its heap buffer at `token + 8` (reviewer's ASan probe).
The Round-6 blanket rejection of comment/body keywords was wrong and is replaced
by this simulation. Reads preserve nonempty native fragments without imposing
write-side split-back checks. Actual native array/whole-text/class receipts
remain required; the simulation neither compiles nor validates general FEA.

Writes replay the VFJ loader: `fgFont.features.clear()`, `set_prefix(prefix)`,
then `set_feature(tag, code)` in order. `clearFeaText(false)` leaves group classes
untouched. The backend initializes package history and wraps writes with
`notifyChangesApplied(name, [package, package.featuresContainer()])` before/after,
calling `notifyFeaturesChanged(font_id, False)` after the fragment writes.
Identical writes and invalid batches add no history. Unexpected native failures
can leave partial writes; this is not an atomic transaction.

`features.text = existing_text` is a no-op. Native `None` is a no-op when already
feature-less; clearing existing features is refused by the synthesis guard
above. A different arbitrary text string raises
`UnsupportedCapability` with capability `font.features.text.split`: only native
whole-text **splitting** (`setFeaText/loadFeaTextInfo`) remains unbound. The pure
simulation validates explicit text blocks; it does not enable arbitrary FEA
import through the text setter. Use the structured setter for history-stable
blocks, subject to the empty-slot baseline limitation above.

## Canonicalization and source evidence

Paths below refer to the read-only native source tree and captured declarations.

| Contract | Primary evidence |
| --- | --- |
| Embedded callable APIs | Echopy `fontpr.pyi:27,87`, `fontgate.pyi:3573–3618`, `fontlab.pyi:6767,9901`. `Proteus/common/mcp/fontpr_module.cpp:139–145,196–212` registers tools and directly calls `MCPTools::callTool`, without loopback HTTP. `mcptools.cpp:713` explicitly permits fontpr calls inside run_python; only recursive run_python/output calls are blocked. |
| Canonical serializer | `mcptools_fonts.cpp:796–811` calls `packageInfoJson`; `Proteus/common/model/flpackage.cpp:6089–6118` calls the same `writeFeatures` used for VFJ save. JSON writer `flblockwriterqjson.cpp:53–55` always uses formatJSON; `bin_types.cpp:642,644` names the fields. |
| Prefix without panel classes, feature order | `flpackage.cpp:6925–6965`: `dumpFeaPrefix(..., false)` plus ordered feature dumps, guarded by hasFeaText. |
| VFJ-equivalent writes | `flpackage.cpp:10215–10252`: clearFeaText(false), setPrefixText and ordered setFeatureText. `pyfontgate/fgotlayout.cxx:280–312` binds those same calls. Default false is in `FontGate/opentype/layout.h:817`; `l_fea.cpp:3212–3238` forces aalt first. |
| Whole-text equivalence | `FontGate/opentype/layout.cpp:1277–1284` and `l_fea.cpp:3574–3612`: dumpFeaText(false) uses the same prefix output plus feature texts. |
| Language synthesis | `layout.cpp:1387–1390` defines hasFeaText by storage existence; `flpackage.cpp:6931` returns before serialization when storage is absent. A no-op does not allocate storage. `l_fea.cpp:3299–3357` checks the literal marker/initial include exception; `xml/xml_write_aux.cpp:63–75` trims only space/tab/LF. `dumpPrefixText` at 4384–4398 emits the auto-tagged block; `flpackage.cpp:6938–6942` calls it for VFJ/metadata. Pairs depend on glyph scripts/build configuration (`l_fea.cpp:472–546`) and feature languages (`549–590,3015–3034`). Only changing staged values receive the prefix refusal; current Undo baselines do not. |
| Table-name correction | `l_fea.cpp:3362–3432` extracts a name table on whole-text loading; its tablesTexts output is commented out in dumpFeaFile at 3585–3602. A structured prefix could otherwise store table code verbatim, but the split-back check now refuses it because Undo would extract it. |
| Empty named records | `flpackage.cpp:10224–10252` defaults feature/name to empty QString, ignores an entirely empty record, and stores a named empty slot with setFeatureText. `l_fea.cpp:2877–2884,3120–3130,4452–4461` keeps the tag while dumping no code. The text API omits textless slots; changing native writes refuse this unrepresentable history baseline. |
| History | `flpackage.cpp:2399–2455` featuresContainer serializes/restores feature state. `writeFeaturesFea` at 6978–6990 dumps whole text; `readFeaturesFea`/`readFeatures` at 7523–7563,7610 restore via setFeaText. `l_fea.cpp:3037–3070,3435–3560` tokenizes/splits and re-keys blocks; `layout.cpp:741–749` appends LF to nonempty fragments. Exact simulated split-back equality replaces the Round-6 keyword guard. |

The read-only corpus regression covers **99/99 GetGo VFJs**: all stage unchanged
and all identical writes succeed before native allocation/history. There are
85 with feature records and 14 feature-less fonts. Only changing writes that
add features without a language-system prefix are refused for those 14.
Corpus discovery prefers an existing `FONTPORT_GETGO_DIR`, then searches every
ancestor of the test file for `fontlab-python-examples/testdata/getgo`; it skips
only when none exists. Both canonical/worktree layouts are tested. A temporary standalone C++ probe
compiles the inspected tokenizer/loader functions with minimal storage stubs;
the Python history simulation matches their outputs for all 99 fonts and 12 edge
cases, including a single-line name table whose unread last byte survives rdbuf.
This is source-level host-free evidence, not FontLab runtime/Undo proof. The
old probe and its per-font hash receipts were removed with the round tooling
(issue 201); they remain in git history.

## Five-second deadline and native acceptance

`get_font_info` includes groups, masters, info, hinting, tables and lib, but no
outline traversal. Its native schema supports only `detail=full` or `hinting`;
there is no narrower feature-only filter in the inspected binding. Repeating or
chunking Python work cannot interrupt one metadata serialization call.

The driver warms imports separately, then performs one read/write/history/save/
reopen operation per call, enforcing <4 s wall time. `--features-only` isolates
B08 and adds a separate Plum variable-font metadata timing call after Medio.
If either call exceeds budget, split handoff at the RPC boundary: obtain a
`get_font_info` snapshot as a direct external MCP tool call outside run_python,
then use `blocks_from_info` for detached parsing. This moves the read outside
the fixed run_python deadline; it does not prove a faster native serializer or
make an oversized write safe. The synchronous backend write still reads current
metadata for its no-op check. No deadline-safe large-font claim is made yet.

The native driver edits one Medio feature, checks byte-equal UTF-8 strings and
order with classes unchanged, tests first Undo/Redo, saves/reopens the edit, then
restores the original blocks and saves/reopens again to compare original bytes.
Receipts return `rows_equal`, `whole_text_equal` and `classes_equal` independently,
along with observed arrays, classes, joined text and observed/expected SHA-256
hashes. A mismatch does not raise before returning evidence: the runner retains
the receipt, marks acceptance failed and continues the remaining phases and
cleanup. A row-boundary/tag difference can thus be distinguished from text loss.
No-op and arbitrary-split refusal phases also record flags, observed history
states and exception type/message/capability instead of asserting. Missing named
fixture features and unavailable staged edits likewise become acceptance flags.
The separate `feature-synthesis-refusal` phase attempts an empty-prefix edit,
records the precise refusal and unchanged history, and retains a failing receipt
if the refusal or history check differs.
Native execution uses the shared mutating-session runner and owned GetGo copies,
then requires a FontLab restart. Host-free replay tests are not native receipts.
