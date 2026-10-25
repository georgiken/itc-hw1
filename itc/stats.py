from math import log2


def print_stats(st):
    n, freqs, lengths = st["n"], st["freqs"], st["lengths"]
    total = st["header"] + st["data"]
    if n:
        H = 0.0 - sum(f / n * log2(f / n) for f in freqs.values())
        lbar = st["bits"] / n
        print(f"  эмпирическая энтропия H = {H:.4f} бит/байт")
        print(f"  средняя длина кода   l̄ = {lbar:.4f} бит/байт")
    else:
        print("  H и l̄ не определены (пустой файл)")
    print(f"  заголовок: {st['header']} байт (различных байтов: {len(lengths)})")
    print(f"  данные:    {st['data']} байт")
    if n:
        print(f"  коэффициент сжатия: {n / total:.4f} (размер zmh = {100 * total / n:.2f}% исходного)")
    else:
        print(f"  коэффициент сжатия не определён: исходный файл пуст, zmh = {total} байт")
