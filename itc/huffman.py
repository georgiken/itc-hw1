# --- начало сгенерированного фрагмента (Claude, см. SOURCES.md) ---
"""Задача 1.3: код Хаффмана (длины кодовых слов) и канонические кодовые слова."""
import heapq


def code_lengths(freqs: dict) -> dict:
    """Длины кодовых слов Хаффмана для символов с ненулевой частотой.
    Один символ — длина 0 (передавать нечего: всё определяется длиной файла).
    Ничьи разрешаются детерминированно — по номеру узла."""
    items = sorted((s, f) for s, f in freqs.items() if f > 0)
    if not items:
        return {}
    if len(items) == 1:
        return {items[0][0]: 0}
    heap = [(f, i, (s,)) for i, (s, f) in enumerate(items)]
    heapq.heapify(heap)
    depth = {s: 0 for s, _ in items}
    uid = len(items)
    while len(heap) > 1:
        f1, _, a = heapq.heappop(heap)
        f2, _, b = heapq.heappop(heap)
        for s in a + b:  # каждое слияние удлиняет коды всех символов поддеревьев на 1
            depth[s] += 1
        heapq.heappush(heap, (f1 + f2, uid, a + b))
        uid += 1
    return depth


def canonical_codes(lengths: dict) -> dict:
    """Канонический код: символы по (длина, символ), коды — последовательные числа.
    Возвращает символ -> (код как целое, длина)."""
    codes = {}
    code, prev = 0, 0
    for s, l in sorted(lengths.items(), key=lambda t: (t[1], t[0])):
        if l == 0:
            codes[s] = (0, 0)
            continue
        code <<= (l - prev)
        codes[s] = (code, l)
        code += 1
        prev = l
    return codes


def kraft_ok(lengths: dict) -> bool:
    """Длины задают полный префиксный код: sum 2^-l = 1 (или один символ длины 0)."""
    ls = list(lengths.values())
    if len(ls) == 1:
        return ls[0] == 0
    if not ls or min(ls) < 1:
        return False
    L = max(ls)
    return sum(1 << (L - l) for l in ls) == 1 << L


class Decoder:
    """Каноническое декодирование: для каждой длины l — первый код и число кодов."""

    def __init__(self, lengths: dict):
        order = sorted(lengths.items(), key=lambda t: (t[1], t[0]))
        self.syms = [s for s, _ in order]
        self.maxlen = max(lengths.values()) if lengths else 0
        self.count = [0] * (self.maxlen + 1)
        for _, l in order:
            self.count[l] += 1
        self.first = [0] * (self.maxlen + 2)
        self.offset = [0] * (self.maxlen + 2)
        code = idx = 0
        for l in range(1, self.maxlen + 1):
            code = (code + self.count[l - 1]) << 1 if l > 1 else 0
            self.first[l] = code
            self.offset[l] = idx
            idx += self.count[l]
# --- конец сгенерированного фрагмента ---
