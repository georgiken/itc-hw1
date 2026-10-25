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
    raise InputError(f"неизвестный режим {args.mode}")
