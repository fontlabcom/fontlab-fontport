# this_file: tests/native_drivers/batch_driver.py
"""B09 in-host steps: one small owned UFO attempt per run_python call.

Polls between attempts return to FontLab's event loop. This proves cooperative
between-file responsiveness for the measured fixture, not large-font preemption
or the Fontlabapp UI scheduler. The host CLI enforces a <4 s call budget.
"""


def batch_phases():
    yield (
        "batch-prepare",
        """
import json
from pathlib import Path
from dataclasses import asdict
from ufoLib2 import Font
from fontlab_fontport.operations import BatchRunner, Recipe
batch_source = Path(output) / 'source.ufo'
batch_target = Path(output) / 'batch-output.ufo'
batch_invalid = Path(output) / 'invalid.ufo'
batch_invalid.mkdir()
batch_runner = BatchRunner()
batch_progress, batch_results = [], []
try:
    batch_runner.run([(Path(output) / 'missing.ufo', Path(output) / 'unwritten.ufo')], Recipe())
except FileNotFoundError:
    pass
else:
    raise AssertionError('Missing batch input accepted')
assert not batch_runner.running and not (Path(output) / 'unwritten.ufo').exists()
""",
    )
    yield (
        "batch-launch",
        """
batch_jobs = batch_runner.run(
    [(batch_source, batch_target), (batch_invalid, Path(output) / 'failure.ufo')],
    Recipe(matrix=(2, 0, 0, 2, 0, 0)), progress=batch_progress.append)
assert batch_runner.running and not batch_target.exists()
try:
    batch_runner.run([(batch_source, Path(output) / 'duplicate.ufo')], Recipe())
except RuntimeError:
    pass
else:
    raise AssertionError('Duplicate launch accepted')
""",
    )
    for index in (1, 2):
        yield (
            f"batch-attempt-{index}",
            "batch_results.append(next(batch_jobs))\nresult = {'index': batch_results[-1].index, 'ok': batch_results[-1].ok, 'error': batch_results[-1].error}",
        )
        yield (
            f"batch-poll-{index}",
            f"assert len(batch_progress) == {index}\n"
            "result = {'running': batch_runner.running, 'attempts': len(batch_progress)}",
        )
    yield (
        "batch-finish",
        """
assert next(batch_jobs, None) is None
assert len(batch_results) == 2 and batch_results[0].ok and not batch_results[1].ok
assert batch_progress == batch_results and not batch_runner.running
""",
    )
    yield (
        "batch-geometry",
        """
with Font.open(batch_source) as before, Font.open(batch_target) as after:
    for name in before.keys():
        assert after[name].width == before[name].width * 2
        if before[name].contours:
            p = before[name].contours[0].points[0]
            q = after[name].contours[0].points[0]
            assert (q.x, q.y) == (p.x * 2, p.y * 2)
""",
    )
    yield (
        "batch-cancel-launch",
        "batch_cancel = batch_runner.run([(batch_source, Path(output) / 'cancel.ufo')], Recipe(), cancelled=lambda: True)",
    )
    yield (
        "batch-cancel-poll",
        """
assert next(batch_cancel, None) is None
assert not batch_runner.running and not (Path(output) / 'cancel.ufo').exists()
(Path(output) / 'batch-results.json').write_text(
    json.dumps([asdict(item) for item in batch_results], default=str, indent=2) + '\\n')
result = {'cancelled': True, 'attempts': len(batch_progress), 'execution': 'inside FontLab, one attempt per call'}
""",
    )
