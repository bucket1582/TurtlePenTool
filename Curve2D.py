from typing import Callable
from math import comb


class Curve2D:
    pass


class ParameterizedCurve2D(Curve2D):
    _curve: Callable[[float], tuple[float, float]]

    def __init__(self, curve: Callable[[float], tuple[float, float]]):
        self._curve = curve

    def get_point(self, t: float) -> tuple[float, float]:
        return self._curve(t)


class BezierCurve2D(ParameterizedCurve2D):
    _point_count: int
    _xs: list[float]
    _ys: list[float]

    def __init__(self, *points: tuple[float, float]):
        self._xs = []
        self._ys = []
        self._point_count = 0
        for point in points:
            self._xs.append(point[0])
            self._ys.append(point[1])
            self._point_count += 1

        super().__init__(
            lambda t: self._compute_point(t)
        )

    def _compute_point(self, t: float) -> tuple[float, float]:
        x = 0
        y = 0
        for n in range(self._point_count):
            multiplier = comb(self._point_count - 1, n) * (1 - t) ** (self._point_count - 1 - n) * t ** n
            x += multiplier * self._xs[n]
            y += multiplier * self._ys[n]
        return x, y
