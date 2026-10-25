"""Задача 1.2: равномерное кодирование стационарного источника без памяти."""
import math
from fractions import Fraction

from .errors import InputError


def memoryless_distribution(src):
    """Возвращает (распределение, None), если источник стационарен и без памяти,
    иначе (None, причина). Проверка точная, в рациональной арифметике."""
    dists = []
    for w, comp in src.components:
        if w == 0:
            continue
        for mname, m in comp.models.items():
            used = any(sw.get(mname, 0) > 0 for sw in
                       (comp.switches[s] for s in comp.source))
            if used and m.order > 0 and len({tuple(sorted(d.items())) for d in m.table.values()}) > 1:
                return None, (f"источник с памятью: модель {mname!r} марковская порядка "
                              f"{m.order}, распределение символа зависит от предыдущих")
        per_tick = [comp.tick_dist(t, ()) for t in range(comp.L)]
        norm = [{s: p for s, p in d.items() if p > 0} for d in per_tick]
        for t in range(1, comp.L):
            if norm[t] != norm[0]:
                diff = sorted(set(norm[0]) | set(norm[t]),
                              key=lambda s: -abs(norm[0].get(s, 0) - norm[t].get(s, 0)))[0]
                return None, (f"источник нестационарен: распределения на тактах 1 и {t + 1} "
                              f"различаются (Pr{{{diff}}} = {norm[0].get(diff, 0)} и "
                              f"{norm[t].get(diff, 0)})")
        dists.append(norm[0])
    if any(d != dists[0] for d in dists[1:]):
        return None, ("источник — смесь компонент с разными распределениями: такты "
                      "зависимы (память), источник неэргодичен")
    return dists[0], None


def entropy(dist):
    return 0.0 - sum(float(p) * math.log2(p.numerator / p.denominator) for p in dist.values() if p > 0)


def require_memoryless(src):
    dist, why = memoryless_distribution(src)
    if dist is None:
        raise InputError(f"задача 1.2 требует стационарный источник без памяти: {why}")
    return dist
