---
this_file: WORK.md
---

## 2026-11-24 — Fontport documentation theme update

Rebuilt `docs/` with fly-january 0.2.1 and updated the active asset hashes and
wheel provenance. The strict build completed without warnings. All 37
documentation tests passed. The arm64 runtime suite passed with the matching
Instamix 1.0.15 fixture (5,151 passed, one skipped, 63 warnings).

## 2026-11-23 — Fontport documentation theme

Rebuilt `docs/` with fly-january 0.1.1 and FontLab chrome. Two strict builds
from the 33-package Python 3.13 lock produced the same 65 files. All 37
documentation tests passed. All 17 HTML files, including the 404 page, load
the Fly assets and contain one Fontport menu and one FontLab footer.

The arm64 Python 3.11 suite passed with the repository's matching Instamix
1.0.15 installer fixture (5,151 passed, one skipped, 63 warnings). Without
that fixture, a newer sibling installer failed the byte-parity test. Browser
verification belongs to the rollout orchestrator.

## 2026-11-17 — Guarded installer final source gate (Task40)

The unchanged complete hook passes on arm64 Python 3.11: 5,150 Fontport tests,
two existing optional skips and 63 warnings (15.61s); 872 Pens tests (1.72s),
95.22% Pens coverage, and 95.51% combined coverage of complete `live.py`.
Expanded Ruff (`src tests examples Scripts`) passes. All 37 hash-locked Python
3.13 documentation tests pass (11.159s).

The initial hook exposed the pinned Pens installer's parity mismatch; the exact
reviewed six-file Pens successor resolves it without runtime changes. The local
SIM118 explanation preserves FontParts name iteration, test imports are sorted,
and the documentation index includes the existing README installer paragraph.
The runtime AST and every existing oracle remain unchanged. Initial failures
and final commands/results are retained in the Task40 evidence.

This supersedes the earlier source-only qualification status below. The final
Fontport candidate has nine authored paths after the authorized gate repairs.
Controller graph and independent review precede delivery. No installer/native
operation or owner-folder installation ran. Exact-SHA CI, release, installed,
Windows/native, owner recovery, standalone Fly/Aidus and existing holds remain.

## 2026-11-17 — Fontport installer contract successor (Task29)

Updated only the sdist test's stale FLM header and added the common canonical
SHA-256 assertion. The exact installer remains unchanged. In a complete isolated
clone, the normal full package-boundary module first reproduced one old-header
failure with nine passes, then passed all ten cases after the fix (0.55s).
Both runs built a genuine sdist and read its payload without running it. The
canonical fallback was a plaintext stub from the qualified Instamix Git object,
not an installed package. Test tooling was pytest-only on arm64 Python 3.11.

This uncommitted six-file source successor supersedes the earlier five-file
Fontport candidate; its exact delta and preservation receipts are in Task29.
Independent review, combined cohort/hooks, exact-SHA CI/release, installed and
native acceptance remain open. Owner recovery, Aidus/Fly, private Pages and
Issue 123 holds remain unchanged. No installer/provider/native operation ran.

## 2026-11-17 — Guarded common installer source candidate

Copied the exact canonical common template shipped with Instamix 1.0.11.
Provider reuse now requires migration/rollback capabilities and entry context is
checked before bootstrap. Legacy rollback requires 1.0.9 or newer; the entry
guard originated in 1.0.10, and shared-layout venv reuse requires 1.0.11.
No package metadata, dependency floors, scripts, bundles or licences changed.
This supersedes earlier shared-installer source notes; historical checks retain
their dated scope.

Compile/AST and exact-template byte checks qualify source only. No installer,
provider, readiness harness, test, package build or native operation ran.
Consumer execution, owner recovery and delivery remain held. Required broad
cohort/suite, release, installed and Windows/native gates remain open.


## 2026-11-15 — Shared installer source alignment

Copied the reviewed shared installer exactly: dependency constraints and managed origins remain protected; inactive conditional dependencies are filtered before sibling execution in the resolver target Python. FontLab imports remain standard-library-only. Package identity, runtime APIs, dependency declarations, scripts, bundles and legal files are unchanged. Existing source-archive installer selection is retained.

Focused checks: 10 passed in 0.61s. This qualifies the local source candidate only. Independent review, combined-main/full delivery gates, genuine release/downloads, installed provider closure and admitted FontLab/native workflows remain separate. No owner-folder installation or native operation ran.



## 2026-11-15 — Shared installer source copy

Copied the reviewed shared template without alteration, preserving mode 0644.
It retains original dependency requirements for uv, constrains installer-managed
local versions/origins, generates optional dependency metadata and refuses
unverifiable no-uv requirements before mutation. The Apache-2.0 SPDX header
matches the authorized first-party installer policy. Package metadata, Scripts,
runtime providers and existing test assertions are unchanged.

The nine existing package-boundary tests pass before and after copying. Exact
template SHA-256 is `5ad9d82825159a5b94c33797fd67a8d93407467d167286d85b307275f109cf71`.
Direct Python syntax and F821 checks pass. Graph impact is UNKNOWN because
`.vfpy` symbols are unindexed; forced Python AST search confirms the dependency
and metadata callers. The index also reports omitted flows, so this is not a
complete production blast-radius claim.

This is an isolated source candidate, pending independent review and controller
combined-main/full/hooked gates. No delivery, release, root installation or
native acceptance is claimed. False-marker eager sibling staging remains open;
cohort propagation and actual installed-provider checks remain separate.

## 2026-11-13 — Documentation content oracle delivered

The reviewed content-oracle repair reached upstream main in merge
`9b31d13fa950a39e52f5327b594f007fb801a6f8`, preserving main `630edf16`
and repair `c3dd1c5`. Independent source and delivery reviews passed. Direct
controller gates passed: 5,130 source tests, one existing skip, 92.30% combined
coverage; 37 locked documentation tests; expanded source/tests/examples/Scripts
Ruff; the external 60-file documentation build; and 869 Pens tests.

The ordinary installed pre-push gate passed separately with 5,129 source tests,
two skips and 869 Pens tests. Its extra skipped case is not identified by the
saved summary. The first push failed for absent upstream tracking; only the
owned branch tracking was added before the normal non-force retry succeeded.
Exact-commit [Documentation run 43506136865](https://github.com/fontlabcom/fontlab-fontport/actions/runs/43506136865)
passed both build and qualify-generated-output jobs. Actual main readback
matched the merge after CI. Only this solved integration item leaves PLAN/TODO.

Graph UNKNOWN impact and omitted flows, historical preservation failures and
untraced writers remain unresolved. These source/main/CI results establish no
new release, artifact, installation, native or default-resolution acceptance.
Existing native, private Pages and Issue 123 holds remain unchanged.


## Documentation content oracle — 2026-11-13

On fresh upstream main, reproduce the cross-date filename false positive and
add a five-case regression before changing the command. The content-patch check
retains the original unstaged/index baseline and all existing byte/epoch/parity
assertions. It passes all cases with raw fixture index bytes and mode unchanged.
Complete locked docs: 37 passed. External shell build: 60 files. Arm64 3.11
source: 5,130 passed, one existing external-corpus skip, 92.30% coverage. Expanded
source lint passes. No production module, installer or generated docs changed.

Retained setup failures include an absent Python executable and unresolved
sibling dependency before the owned peer layout was corrected. The latter run
also observed a raw owned-clone index change, with cause unassigned; both index
versions are preserved. The successful corrected gates preserve their starting
indexes. No index was restored. This does not affect the independently checked
fixture-index result. Remaining: independent review, fresh combined-main gates,
normal hooked delivery and exact-commit CI; no native or install claim.

# Current round — Issue 255 post-release reconciliation

## 2026-11-14 — Functional work order documented

Updated AGENTS, PLAN and TODO to prioritize useful functional changes and compatible package boundaries, with detailed testing deferred. Existing backlog and prior records are retained. Documentation preservation and policy consistency were checked; no runtime, installed or native checks ran in this documentation-only pass.

Next: reconcile UFO feature and batch-recipe behavior across Fontport, App and Scriptmix with focused source/preservation checks before the detailed artifact and native/history pass.

[fontlab-fontport v1.2.9](https://github.com/fontlabcom/fontlab-fontport/releases/tag/v1.2.9) is qualified at `a11cbe2340201ec07d81c95dd567981cdef81d12`.

The three Scripts, seven examples and generated startup/recipe teaching use Fly. The UI tombstone teaches fly.ap.fontui with unchanged runtime ownership/error behavior.

5,131 source tests pass without skips; the complete tombstone has 100% statement/branch coverage with zero exclusions. All 36 documentation tests and exact 60-file containing-source rebuild parity pass. Genuine wheel and actual-sdist ordinary cohorts each contain 28 compatible packages and match all 43 installed Fontport payload files; three lazy Scripts, UFO geometry and 23 archive/tombstone cases pass.

The source, artifact, ordinary external-install, release and download gates above are verified. This round reconciles their progress records after release; it changes no runtime source, installer, dependency declaration, generated documentation or immutable release asset. Consumer setup still requires separately installing matching Fly >=1.3 in the same interpreter. Provider source installers do not automatically supply or enforce this prerequisite; no reverse mandatory Fly dependency is claimed.

Remaining: After explicit D43 recovery and admission, qualify released Fly/Fontport Scripts, generated startup recipes and original native UFO/UI/history/save-reopen workflows with exact installed paths and provider identities.

D43 native acceptance remains held and unproved. Issue 123 remains paused; existing private Pages holds and every unrelated acceptance task remain in PLAN/TODO. Prior WORK bytes are retained exactly in the private external delivery ledger, SHA256 `1d3cfc6fb840cc92bd1e21b4b0281eae573417f29dd792498ef2590cc691b302`.
