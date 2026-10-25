"""Точная рациональная арифметика: разбор вероятностей и выборка по дробям."""
from fractions import Fraction
from math import lcm

from .errors import InputError

# в тексте задания дроби набраны через U+2215 (DIVISION SLASH); принимаем и её
_SLASHES = {"∕": "/", "⁄": "/"}


def parse_prob(value, where: str) -> Fraction:
    if not isinstance(value, str):
        raise InputError(f"{where}: вероятность должна быть строкой, получено {value!r}")
    s = value.strip()
    for a, b in _SLASHES.items():
        s = s.replace(a, b)
    try:
        p = Fraction(s)
    except (ValueError, ZeroDivisionError):
        raise InputError(f"{where}: не удалось разобрать вероятность {value!r}") from None
    if p < 0:
        raise InputError(f"{where}: отрицательная вероятность {value}")
    return p


def parse_dist(obj, where: str) -> dict:
    if not isinstance(obj, dict) or not obj:
        raise InputError(f"{where}: ожидается непустой объект «имя: вероятность»")
    dist = {k: parse_prob(v, f"{where}[{k!r}]") for k, v in obj.items()}
    total = sum(dist.values())
    if total != 1:
        raise InputError(f"{where}: распределение не нормировано, сумма = {total}")
    return dist


class Sampler:
    """Выборка из распределения с рациональными вероятностями без float:
    вероятности приводятся к общему знаменателю D, затем берётся randrange(D)."""

    def __init__(self, dist: dict):
        items = [(k, p) for k, p in dist.items() if p > 0]
        D = lcm(*(p.denominator for _, p in items))
        self.keys = [k for k, _ in items]
        self.cum = []
        acc = 0
        for _, p in items:
            acc += p.numerator * (D // p.denominator)
            self.cum.append(acc)
        self.D = D

    def draw(self, rng):
        r = rng.randrange(self.D)
        lo, hi = 0, len(self.cum) - 1
        while lo < hi:  # двоичный поиск первого cum > r
            mid = (lo + hi) // 2
            if self.cum[mid] > r:
                hi = mid
            else:
                lo = mid + 1
        return self.keys[lo]
