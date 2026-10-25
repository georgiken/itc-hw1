# --- начало сгенерированного фрагмента (Claude, см. SOURCES.md) ---
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


# ---------------------------------------------------------------------------
# Режим 2. Вероятность блока источника без памяти зависит только от его типа —
# вектора счётчиков (c_1..c_k), sum c_i = n. Блоков типа c ровно n!/prod c_i!,
# и все они равновероятны. Поэтому оптимальное множество из q^l блоков
# набирается целыми типами в порядке убывания вероятности (последний тип —
# частично). Число типов C(n+k-1, k-1) ~ n^(k-1)/(k-1)! вместо k^n блоков.
#
# Точность: p_i = a_i / D (D — общий знаменатель), вероятность блока типа c
# равна prod a_i^c_i / D^n — целые числа Python, без переполнения и округлений.
# Сортировка идёт по ключу sum c_i log p_i (float); соседние типы с почти равными
# ключами досортировываются точно по целым числителям, так что выбор множества
# и итоговое P_e(n) точные.
# ---------------------------------------------------------------------------
import itertools
from math import comb, lcm, log2


def code_length(n, R: Fraction, q):
    """l(n) = floor(nR / log2 q) — точно: наибольшее l с q^l <= 2^(nR),
    т.е. q^(l*den) <= 2^(n*num) для R = num/den."""
    num, den = R.numerator, R.denominator
    rhs = 2 ** (n * num)
    l = int(n * float(R) / log2(q)) + 1
    while l > 0 and q ** (l * den) > rhs:
        l -= 1
    while q ** ((l + 1) * den) <= rhs:
        l += 1
    return l


def _types(n, lp):
    """Все типы (c_1..c_k), sum c_i = n, вместе с ключом sum c_i * lp_i.
    Перебор вложенными циклами; последний уровень — генератор списка."""
    k = len(lp)
    keys, types = [], []

    def rec(i, left, key, prefix):
        if i == k - 2:
            a, b = lp[i], lp[i + 1]
            keys.extend([key + c * a + (left - c) * b for c in range(left + 1)])
            types.extend([prefix + (c, left - c) for c in range(left + 1)])
            return
        li = lp[i]
        for c in range(left + 1):
            rec(i + 1, left - c, key + c * li, prefix + (c,))

    if k == 1:
        return [n * lp[0]], [(n,)]
    rec(0, n, 0.0, ())
    return keys, types


def best_set(n, M, syms, probs):
    """Оптимальное множество из M блоков длины n. Возвращает
    (P_e как Fraction, список (тип, взято блоков, всего блоков типа))."""
    k = len(syms)
    D = lcm(*(p.denominator for p in probs))
    a = [p.numerator * (D // p.denominator) for p in probs]
    if M >= k ** n:
        return Fraction(0), [(None, k ** n, k ** n)]
    keys, types = _types(n, [log2(x) for x in a])
    order = sorted(range(len(keys)), key=keys.__getitem__, reverse=True)
    apow = [[1] * (n + 1) for _ in a]
    for i, ai in enumerate(a):
        for c in range(1, n + 1):
            apow[i][c] = apow[i][c - 1] * ai
    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i

    def exact(cs):
        r = 1
        for i, c in enumerate(cs):
            if c:
                r *= apow[i][c]
        return r

    def count(cs):
        r = 1
        for c in cs:
            r *= fact[c]
        return fact[n] // r

    need, mass, chosen = M, 0, []
    i, T = 0, len(order)
    while need > 0 and i < T:
        j = i + 1  # группа почти равных ключей досортировывается точно
        ki = keys[order[i]]
        tol = 1e-9 * max(1.0, abs(ki))
        while j < T and ki - keys[order[j]] <= tol:
            j += 1
        group = [(exact(types[t]), types[t]) for t in order[i:j]]
        if j - i > 1:
            group.sort(key=lambda g: -g[0])
        for num, cs in group:
            cnt = count(cs)
            take = cnt if cnt < need else need
            mass += take * num
            need -= take
            chosen.append((cs, take, cnt))
            if need == 0:
                break
        i = j
    return 1 - Fraction(mass, D ** n), chosen
# --- конец сгенерированного фрагмента ---
