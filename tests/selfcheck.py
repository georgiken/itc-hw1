"""Самопроверки алгоритмов против полного перебора и эталонов."""
import itertools
import math
import os
import random
import sys
import zlib
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from itc.uniform import best_set                      # noqa: E402
from itc.huffman import code_lengths, kraft_ok        # noqa: E402
from itc.crc32 import crc32                           # noqa: E402

# 1.2: оптимальное множество по типам == полный перебор k^n блоков
probs = [Fraction(17, 50), Fraction(19, 100), Fraction(31, 200), Fraction(63, 400), Fraction(63, 400)]
cases = 0
for n in range(1, 7):
    allp = sorted((math.prod(probs[i] for i in b) for b in itertools.product(range(5), repeat=n)),
                  reverse=True)
    for M in (1, 3, 7, 25, 100, 5 ** n - 1):
        if M > 5 ** n:
            continue
        pe, _ = best_set(n, M, list("abcde"), probs)
        assert pe == 1 - sum(allp[:M]), (n, M)
        cases += 1
print(f"1.2: P_e по типам совпадает с полным перебором в {cases} случаях (n <= 6)")


# 1.3: длины Хаффмана оптимальны (перебор всех деревьев слияния при k <= 6)
def brute(fr):
    best = [None]

    def rec(nodes):
        if len(nodes) == 1:
            best[0] = nodes[0][1] if best[0] is None else min(best[0], nodes[0][1])
            return
        for i, j in itertools.combinations(range(len(nodes)), 2):
            w = nodes[i][0] + nodes[j][0]
            rec([x for t, x in enumerate(nodes) if t not in (i, j)] + [(w, nodes[i][1] + nodes[j][1] + w)])
    rec([(f, 0) for f in fr.values()])
    return best[0]


rnd = random.Random(1)
for _ in range(200):
    fr = {s: rnd.randint(1, 30) for s in range(rnd.randint(2, 6))}
    L = code_lengths(fr)
    assert kraft_ok(L) and sum(fr[s] * L[s] for s in fr) == brute(fr)
print("1.3: длины Хаффмана оптимальны и удовлетворяют Крафту на 200 случайных наборах")

for d in (b"", b"a", b"123456789", bytes(range(256)) * 3):
    assert crc32(d) == zlib.crc32(d)
print("1.3: собственный CRC-32 совпадает с zlib.crc32 (используется только для проверки)")
