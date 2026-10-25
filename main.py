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
    sub.add_parser("t1", help="задача 1.1: моделирование источника")
    sub.add_parser("t2", help="задача 1.2: равномерное кодирование")
    sub.add_parser("t3", help="задача 1.3: архиватор zmh")
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
    raise InputError(f"режим {args.task} ещё не реализован")


def main(argv=None) -> int:
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except InputError as e:
        print(f"ошибка: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nпрервано пользователем", file=sys.stderr)
        return 130
    except Exception as e:  # программа не должна падать с трейсбеком (п. 1.1.4)
        print(f"внутренняя ошибка: {type(e).__name__}: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
