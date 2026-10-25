"""CLI задачи 1.2."""
from .errors import InputError
from .source import load_source
from .uniform import memoryless_distribution, entropy


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
    raise InputError(f"неизвестный режим {args.mode}")
