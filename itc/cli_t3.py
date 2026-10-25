# --- начало сгенерированного фрагмента (Claude, см. SOURCES.md) ---
"""CLI задачи 1.3."""
import os

from .errors import InputError
from .zmh import compress, decompress


def run(args):
    if args.mode == "compress":
        out = args.out or args.file + ".zmh"
        st = compress(args.file, out)
        print(f"{args.file} -> {out}: {st['n']} -> {st['header'] + st['data']} байт")
        if args.stats:
            from .stats import print_stats
            print_stats(st)
        return 0
    if args.mode == "decompress":
        if not args.file.endswith(".zmh") and args.out is None:
            raise InputError("ожидается файл с расширением .zmh (или укажите -o)")
        out = args.out or args.file[:-4]
        if os.path.exists(out) and not args.force:
            raise InputError(f"{out} уже существует; укажите -o или --force")
        h = decompress(args.file, out)
        print(f"{args.file} -> {out}: {h['n']} байт, контрольная сумма совпала")
        return 0
    raise InputError(f"неизвестный режим {args.mode}")
# --- конец сгенерированного фрагмента ---
