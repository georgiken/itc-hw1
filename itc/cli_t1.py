"""CLI задачи 1.1."""
import itertools
import sys

from .errors import InputError
from .source import load_source, make_rng


def parse_N(text):
    if text is None or str(text).strip().lower() == "none":
        return None
    try:
        return int(text)
    except ValueError:
        raise InputError(f"N должно быть целым числом или None, получено {text!r}") from None


def run(args):
    src = load_source(args.file)
    if args.mode == "gen":
        N = parse_N(args.N)
        rng = make_rng(args.seed)
        j = src.joiner()
        gen = src.generate(rng)
        if N is not None and N > 0:
            print(j.join(itertools.islice(gen, N)))
            return 0
        try:  # бесконечная выдача до Ctrl+C (SIGINT)
            while True:
                sys.stdout.write(j.join(itertools.islice(gen, 1000)) + j)
                sys.stdout.flush()
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            return 0
    if args.mode == "prob":
        return run_prob(src, args)
    raise InputError(f"неизвестный режим {args.mode}")


def parse_seq(text, alphabet):
    if "," in text:
        seq = [x.strip() for x in text.split(",")]
    elif all(len(a) == 1 for a in alphabet):
        seq = list(text)
    else:
        raise InputError("символы алфавита многобуквенные: задайте --seq через запятую")
    if not seq or any(x == "" for x in seq):
        raise InputError("пустая последовательность или пустой символ в --seq")
    unknown = sorted(set(seq) - set(alphabet))
    if unknown:
        print(f"предупреждение: символов {unknown} нет в алфавите, вероятность равна 0",
              file=sys.stderr)
    return tuple(seq)


TABLE_N = (10**2, 10**3, 10**4, 10**5, 10**6)


def fmt(p):
    return f"{p} ≈ {float(p):.6e}"


def run_prob(src, args):
    N = parse_N(args.N)
    if N is None or N <= 0:
        raise InputError("в режиме prob требуется N > 0")
    seq = parse_seq(args.seq, src.alphabet)
    r = len(seq)
    p1 = src.prob_at(seq, 0)
    pavg = src.prob_period_avg(seq)
    print(f"последовательность: {','.join(seq)} (r = {r}), период L = {src.period}")
    print(f"1) Pr{{X1..Xr = a}} (с первого такта):   {fmt(p1)}")
    print(f"2) среднее по позициям периода:        {fmt(pavg)}")

    # одна реализация длины max(N, 10^6); оценки для меньших N — по её префиксам
    total = max(N, TABLE_N[-1])
    xs = list(itertools.islice(src.generate(make_rng(args.seed)), total))
    marks = sorted(set(TABLE_N) | {N})
    counts = {}
    c = 0
    mi = 0
    for i in range(total - r + 1):
        if tuple(xs[i:i + r]) == seq:
            c += 1
        while mi < len(marks) and i + 1 == marks[mi] - r + 1:
            counts[marks[mi]] = c
            mi += 1

    def freq(n):
        return counts[n] / (n - r + 1) if n >= r else None

    f = freq(N)
    print(f"3) частотная оценка, N = {N}:            "
          + (f"{f:.6e}" if f is not None else "не определена (N < r)"))
    print()
    print(f"{'N':>8}  {'частота':>12}  {'|част - (1)|':>12}  {'|част - (2)|':>12}")
    for n in TABLE_N:
        fn = freq(n)
        if fn is None:
            print(f"{n:>8}  {'—':>12}")
            continue
        print(f"{n:>8}  {fn:>12.6e}  {abs(fn - float(p1)):>12.6e}  {abs(fn - float(pavg)):>12.6e}")
    return 0
