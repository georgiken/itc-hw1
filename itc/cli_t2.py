import json
import time
from fractions import Fraction
from math import log2

from .errors import InputError
from .probs import parse_prob
from .source import load_source
from .uniform import memoryless_distribution, entropy, require_memoryless, code_length, best_set
from . import variant


def run(args):
    src = load_source(args.file)
    if args.mode == "check":
        dist, why = memoryless_distribution(src)
        if dist is None:
            raise InputError(why)
        print("источник стационарен и не имеет памяти")
        print("распределение: " + ", ".join(f"{s}: {p}" for s, p in sorted(dist.items())))
        print(f"H(X) = {entropy(dist):.6f} бит/символ")
        return 0
    if args.mode == "code":
        return run_code(src, args)
    raise InputError(f"неизвестный режим {args.mode}")


def _int_arg(text, name, lo):
    try:
        v = int(text)
    except (TypeError, ValueError):
        raise InputError(f"{name} должно быть целым, получено {text!r}") from None
    if v < lo:
        raise InputError(f"{name} должно быть >= {lo}")
    return v


def _rate(text, name):
    try:
        return parse_prob(text, name)
    except InputError:
        raise InputError(f"{name}: ожидается неотрицательное число (дробь или десятичная запись), "
                         f"получено {text!r}") from None


def _big(x):
    s = str(x)
    return s if len(s) <= 12 else f"{s[0]}.{s[1:4]}e{len(s) - 1}"


def run_code(src, args):
    vp = variant.params()
    dist = require_memoryless(src)
    R = _rate(args.R, "R")
    eps = _rate(args.eps if args.eps is not None else vp["eps"], "eps")
    if eps > 1:
        raise InputError("eps должно быть в [0, 1]")
    q = _int_arg(args.q if args.q is not None else vp["q"], "q", 2)
    nmax = _int_arg(args.nmax, "nmax", 1)
    # символы нулевой вероятности в оптимальное множество не попадают,  поэтому отбрасываем
    items = sorted(((s, p) for s, p in dist.items() if p > 0), key=lambda t: (-t[1], t[0]))
    syms = [s for s, _ in items]
    probs = [p for _, p in items]
    H = entropy(dist)
    print(f"H(X) = {H:.6f} бит/символ, R = {R} ≈ {float(R):.6f}, q = {q}, eps = {eps}, "
          f"n_max = {nmax}")
    print(f"{'n':>3} {'l(n)':>5} {'q^l':>14} {'R_факт':>9} {'типов':>7}  P_e(n)")
    t0 = time.perf_counter()
    rows = []
    for n in range(1, nmax + 1):
        l = code_length(n, R, q)
        pe, chosen = best_set(n, q ** l, syms, probs)
        rows.append((n, l, pe, chosen))
        print(f"{n:>3} {l:>5} {_big(q ** l):>14} {l * log2(q) / n:>9.5f} {len(chosen):>7}  "
              f"{float(pe):.6e}")
    elapsed = time.perf_counter() - t0
    ok = [r for r in rows if r[2] <= eps]
    print()
    if ok:
        print(f"минимальное n с P_e(n) <= eps: {ok[0][0]} (P_e = {float(ok[0][2]):.6e})")
    else:
        print(f"на отрезке n = 1..{nmax} нет n с P_e(n) <= eps")
    tail = nmax + 1
    while tail > 1 and rows[tail - 2][2] <= eps:
        tail -= 1
    print("существует ли n0: P_e(n) <= eps при всех n >= n0?")
    if len(syms) == 1:
        print("  да: источник детерминирован (один символ с вероятностью 1), P_e(n) = 0 при любом n")
    elif float(R) > H:
        print(f"  да: R = {float(R):.4f} > H(X) = {H:.4f}, по прямой теореме кодирования P_e(n) -> 0"
              + (f"; на рассмотренном отрезке условие выполнено при всех n >= {tail}"
                 if tail <= nmax else "; на рассмотренном отрезке n0 ещё не достигнуто"))
    elif float(R) < H:
        print(f"  нет: R = {float(R):.4f} < H(X) = {H:.4f}, по обратной теореме P_e(n) -> 1. "
              "При малых n условие может выполняться (обратная теорема асимптотическая), "
              "но при больших n обязательно нарушается")
    else:
        print("  граничный случай R = H(X): P_e(n) не стремится к 0, при eps < 1/2 n0 не существует")
    print(f"время расчёта таблицы: {elapsed:.2f} с")

    n, l, pe, chosen = ok[0] if ok else rows[-1]
    out = args.out or (args.file.rsplit(".", 1)[0] + ".code.json")
    desc = {
        "n": n, "l": l, "q": q, "codewords": q ** l, "P_e": str(pe), "P_e_float": float(pe),
        "alphabet_order": syms,
        "rule": ("кодируемое множество — объединение перечисленных типов в данном порядке; "
                 "внутри типа блоки упорядочены лексикографически по alphabet_order, "
                 "из последнего типа берутся первые 'taken' блоков. Кодовое слово блока — "
                 "его номер в этом порядке, записанный в системе счисления q l цифрами. "
                 "Блок вне множества — ошибка декодирования."),
        "types": ([{"all_blocks": True, "taken": chosen[0][1]}] if chosen[0][0] is None else
                  [{"counts": dict(zip(syms, cs)), "taken": take, "of": cnt}
                   for cs, take, cnt in chosen]),
    }
    try:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(desc, f, ensure_ascii=False, indent=1, default=str)
    except OSError as e:
        raise InputError(f"не удалось записать {out}: {e.strerror}") from None
    print(f"описание кода для n = {n} записано в {out}")
    return 0
