# this_file: src/fontlab_fontport/recipe.py
"""Small inspectable B09 affine recipes; no research transform engines."""

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from fontTools.misc.transform import Identity, Transform

from .errors import UnsupportedCapability


def finite_number(value: float) -> float:
    if type(value) not in (int, float):
        raise TypeError("Expected a finite number")
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError("Expected a finite number")
    return value


@dataclass(frozen=True)
class Recipe:
    """Affine matrix blended from identity by intensity (0..100 percent).

    This is an affine operation, without stem/topology preservation claims.
    Disabled recipes and zero intensity are identity. Reset uses Recipe().
    Singular matrices are refused because component conjugation needs an inverse.
    """

    matrix: tuple[float, ...] = tuple(Identity)
    intensity: float = 100
    enabled: bool = True
    method: str = "affine"

    def __post_init__(self) -> None:
        if self.method != "affine":
            raise UnsupportedCapability(
                "recipe.method", f"Unavailable transform method: {self.method}"
            )
        if type(self.enabled) is not bool:
            raise TypeError("enabled must be a boolean")
        if not 0 <= finite_number(self.intensity) <= 100:
            raise ValueError("Intensity must be in 0..100")
        if not isinstance(self.matrix, (tuple, list)) or len(self.matrix) != 6:
            raise ValueError("Affine matrix requires six numbers")
        object.__setattr__(self, "matrix", tuple(finite_number(v) for v in self.matrix))
        for matrix in (Transform(*self.matrix), self.transform):
            determinant = matrix.xx * matrix.yy - matrix.xy * matrix.yx
            if not math.isfinite(determinant) or determinant == 0:
                raise ValueError("Affine matrix must have a finite nonzero determinant")

    @property
    def transform(self) -> Transform:
        factor = self.intensity / 100 if self.enabled else 0
        return Transform(
            *(a + (b - a) * factor for a, b in zip(Identity, self.matrix, strict=True))
        )

    def save(self, path: str | Path) -> None:
        with Path(path).open("x", encoding="utf-8") as stream:
            json.dump(asdict(self), stream, indent=2, allow_nan=False)
            stream.write("\n")

    @classmethod
    def load(cls, path: str | Path) -> "Recipe":
        with Path(path).open(encoding="utf-8") as stream:
            return cls(**json.load(stream))

    def script(self) -> str:
        """Return inspectable source; loading settings never executes Python."""
        return (
            "# Requires installed fontlab-fly>=1.3.0 and its canonical providers.\n"
            "from fly.fp.operations import Recipe, transform_font\n\n"
            f"recipe = {self!r}\n\n"
            "def run(source):\n    return transform_font(source, recipe)\n"
        )
