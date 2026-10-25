#!/usr/bin/env python3
"""Точка входа. Все режимы запускаются неинтерактивно: см. README.md."""
import argparse
import sys

from itc.errors import InputError
from itc import variant


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="main.py", description="ДЗ №1: кодирование источников")
    p.add_argument("--variant", action="store_true", help="вывести номер варианта и параметры")
    sub = p.add_subparsers(dest="task")
    t1 = sub.add_parser("t1", help="задача 1.1: моделирование источника")
    t1s = t1.add_subparsers(dest="mode", required=True)
    g = t1s.add_parser("gen", help="режим 1: реализация источника")
    g.add_argument("file")
    g.add_argument("--N", default="None", help="длина; None или N<=0 — до прерывания (Ctrl+C)")
    g.add_argument("--seed", type=int, default=None)
    pr = t1s.add_parser("prob", help="режим 2: точная вероятность и частотная оценка")
    pr.add_argument("file")
    pr.add_argument("--N", required=True, help="длина реализации, N > 0")
    pr.add_argument("--seq", required=True,
                    help="последовательность a1..ar: строка символов или символы через запятую")
    pr.add_argument("--seed", type=int, default=None)
    t2 = sub.add_parser("t2", help="задача 1.2: равномерное кодирование")
    t2s = t2.add_subparsers(dest="mode", required=True)
    c = t2s.add_parser("check", help="режим 1: проверка и энтропия")
    c.add_argument("file")
    cd = t2s.add_parser("code", help="режим 2: таблица P_e(n), минимальное n, описание кода")
    cd.add_argument("file")
    cd.add_argument("--R", required=True, help="скорость, бит на символ (дробь или десятичная)")
    cd.add_argument("--eps", default=None, help="граница ошибки (по умолчанию из варианта)")
    cd.add_argument("--q", default=None, help="мощность алфавита кодера (по умолчанию из варианта)")
    cd.add_argument("--nmax", default="50")
    cd.add_argument("--out", default=None, help="файл описания кода (по умолчанию <file>.code.json)")
    t3 = sub.add_parser("t3", help="задача 1.3: архиватор zmh")
    t3s = t3.add_subparsers(dest="mode", required=True)
    z = t3s.add_parser("compress", help="сжатие: <file> -> <file>.zmh")
    z.add_argument("file")
    z.add_argument("-o", "--out", default=None)
    z.add_argument("--stats", action="store_true", help="вывести H, средняя длина, размеры, коэффициент")
    x = t3s.add_parser("decompress", help="восстановление: <file>.zmh -> <file>")
    x.add_argument("file")
    x.add_argument("-o", "--out", default=None)
    x.add_argument("--force", action="store_true", help="перезаписать существующий файл")
    return p


def run(argv) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.variant:
        print(variant.describe())
        return 0
    if args.task is None:
        parser.print_help()
        return 2
    if args.task == "t1":
        from itc import cli_t1
        return cli_t1.run(args)
    if args.task == "t2":
        from itc import cli_t2
        return cli_t2.run(args)
    if args.task == "t3":
        from itc import cli_t3
        return cli_t3.run(args)
    raise InputError(f"режим {args.task} не реализован")


def main(argv=None) -> int:
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except InputError as e:
        print(f"ошибка: {e}", file=sys.stderr)
        return 2
    except BrokenPipeError:  # вывод перенаправлен в head и т.п.
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0
    except KeyboardInterrupt:
        print("\nпрервано пользователем", file=sys.stderr)
        return 130
    except Exception as e:  # программа не должна падать с трейсбеком (п. 1.1.4)
        print(f"внутренняя ошибка: {type(e).__name__}: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
