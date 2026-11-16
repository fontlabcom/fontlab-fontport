---
this_file: src_docs/md/installation.md
---

# Installation

## Install

FontLab supplies `fontlab`, `fontgate`, `fontpr` and PythonQt. It needs Python
packages built for its own Python 3.11 arm64 runtime. The owner manages editable
installs into FontLab; do not run host install/uninstall commands yourself. Canonical editable sources may differ from this worktree.

Fontport base installation needs no App. The optional `fontlab` extra requires
`fontlab-fontlabapp>=1.2.0` for native edit guards and the legacy feature forwarder.
It does not establish registry availability, native acceptance or a release. `fontlab-fontlabapp` is not on a package
index, so `pip install "fontlab-fontport[fontlab]"` cannot resolve it: install `fontlab-fontlabapp` from a checkout first. For
development, `[tool.uv.sources]` resolves it from the sibling `../fontlab-fontlabapp` checkout, and `uv.lock` records
that path source.
See [dependencies](https://github.com/fontlabcom/fontlab-fontport/blob/bbe74e286b8281ae22b383cf42755d9d084c8aae/DEPENDENCIES.md) for package roles and version policy.
