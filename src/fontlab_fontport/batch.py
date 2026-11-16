# this_file: src/fontlab_fontport/batch.py
"""Bounded detached UFO batch work, suitable for an external UI worker."""

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from ufoLib2 import Font

from .paths import absolute_path
from .recipe import Recipe

MAX_JOBS = 256


@dataclass(frozen=True)
class BatchResult:
    index: int
    total: int
    source: Path
    destination: Path
    ok: bool
    error: str | None = None


def _jobs(jobs: Iterable[tuple[str | Path, str | Path]]) -> list[tuple[Path, Path]]:
    result = []
    for source, destination in jobs:
        if len(result) >= MAX_JOBS:
            raise ValueError(f"Batch is limited to {MAX_JOBS} jobs")
        source = absolute_path(source, strict=True)
        target = absolute_path(destination)
        if source.suffix.lower() != ".ufo" or target.suffix.lower() != ".ufo":
            raise ValueError("Batch source and destination must be UFO paths")
        if target.exists():
            raise FileExistsError(target)
        if any(
            str(target).casefold() == str(existing).casefold() for _, existing in result
        ):
            raise ValueError("Duplicate batch destination")
        result.append((source, target))
    if not result:
        raise ValueError("Batch requires at least one source and destination")
    sources = {source for source, _ in result}
    for _, target in result:
        if any(parent in sources for parent in target.parents):
            raise ValueError("Batch destination must be outside every source UFO")
    source_ids = {(info.st_dev, info.st_ino) for info in (source.stat() for source in sources)}
    for _, target in result:
        for parent in target.parents:
            try:
                info = parent.stat()
            except (FileNotFoundError, NotADirectoryError):
                continue
            if (info.st_dev, info.st_ino) in source_ids:
                raise ValueError("Batch destination must be outside every source UFO")
    return result


class BatchRunner:
    """One iterator at a time; failures are per-item data and cancellation is explicit.

    Exhaust or close the iterator to release running state. Progress is emitted
    after each actual attempt. Drive this outside the FontLab UI thread: one
    large font may exceed run_python's fixed five-second deadline. No native
    objects are accessed; scheduling/background controls belong to Fontlabapp.
    """

    def __init__(self) -> None:
        self.running = False

    def run(
        self,
        jobs: Iterable[tuple[str | Path, str | Path]],
        recipe: Recipe,
        *,
        progress: Callable[[BatchResult], None] | None = None,
        cancelled: Callable[[], bool] = lambda: False,
    ) -> Iterator[BatchResult]:
        if self.running:
            raise RuntimeError("A batch is already running")
        staged = _jobs(jobs)
        self.running = True
        return _BatchIterator(self, self._execute(staged, recipe, progress, cancelled))

    def _execute(self, staged, recipe, progress, cancelled):
        from .operations import transform_font

        try:
            for index, (source, target) in enumerate(staged, 1):
                if cancelled():
                    break
                error = None
                try:
                    with Font.open(source) as font:
                        transformed = transform_font(font, recipe)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    transformed.save(target, overwrite=False)
                except Exception as failure:  # noqa: BLE001 - each job reports its failure
                    error = f"{type(failure).__name__}: {failure}"
                result = BatchResult(
                    index, len(staged), source, target, error is None, error
                )
                if progress is not None:
                    progress(result)
                yield result
        finally:
            self.running = False


class _BatchIterator:
    """Release an eager reservation even when closed before the first next()."""

    def __init__(self, runner, iterator):
        self.runner, self.iterator = runner, iterator
        self._closed = False

    def __iter__(self):
        return self

    def __next__(self):
        if self._closed:
            raise StopIteration
        try:
            return next(self.iterator)
        except BaseException:  # cleanup also applies to StopIteration/cancellation
            self.close()
            raise

    def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self.iterator.close()
        finally:
            self.runner.running = False

    def __del__(self):
        self.close()
