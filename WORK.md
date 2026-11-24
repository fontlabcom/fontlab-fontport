---
this_file: WORK.md
---

## 2026-11-24 — Release and backlog review

Release v1.2.18 at `862f8c8` published the wheel and sdist through GitHub Actions. Both downloaded archives match the GitHub release hashes, and the sdist installer matches this checkout. PyPI identifies `fontlabcom/fontlab-fontport`, `release.yml` and environment `pypi` as the trusted publisher for both files. [Release run](https://github.com/fontlabcom/fontlab-fontport/actions/runs/44411658072).

On the merged source at `c5878ef`, the arm64 Python 3.11 suite passed 5,151 tests with one skip and 63 warnings using Instamix 1.0.18. All 37 Python 3.13 documentation tests passed. The release scripts passed Bash syntax checks and the local publishing handoff passed both its simulated success and workflow-failure checks.

[TODO.md](TODO.md) lists the remaining checks. Issue 271 still needs the cohort review and hook evidence and an installed macOS/Windows check. Issue 123 remains paused. Issue 255 requires D43 native admission, and the private Pages holds remain in force.
