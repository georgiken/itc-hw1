#!/usr/bin/env python3
"""Прогон собственных тестов. Пишет RESULTS.md с дословным выводом программы."""
import os
import shlex
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join("tests", "out")
PY = sys.executable

sections = []


def run(cmd, note=None):
    args = [PY] + shlex.split(cmd)
    t = time.perf_counter()
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    dt = time.perf_counter() - t
    body = (p.stdout + p.stderr).rstrip()
    sections.append((f"$ python3 {cmd}", body, p.returncode, dt, note))
    return p


def section(title):
    sections.append(title)


def corrupt(src, dst, fn):
    with open(os.path.join(ROOT, src), "rb") as f:
        b = bytearray(f.read())
    with open(os.path.join(ROOT, dst), "wb") as f:
        f.write(fn(b))


os.makedirs(os.path.join(ROOT, OUT), exist_ok=True)

section("## Вариант")
run("main.py --variant")

section("## Самопроверки")
run("tests/selfcheck.py")

section("## Задача 1.1. Режим 1 — реализация источника")
run("main.py t1 gen tests/t1/variant.json --N 60 --seed 1")
run("main.py t1 gen tests/t1/variant.json --N 60 --seed 1", "повтор с тем же seed — та же строка")
run("main.py t1 gen tests/t1/example2.json --N 60 --seed 2")
run("main.py t1 gen tests/t1/degenerate_one_symbol.json --N 20")
for f in ("ext_stationary_iid", "ext_markov_ergodic", "ext_nonergodic_mixture"):
    run(f"main.py t1 gen tests/t1/{f}.json --N 60 --seed 3")
section("Некорректные входы (ожидается диагностика и код возврата 2):")
for f in sorted(os.listdir(os.path.join(ROOT, "tests", "t1"))):
    if f.startswith("bad_"):
        run(f"main.py t1 gen tests/t1/{f} --N 10")
run("main.py t1 gen tests/t1/missing.json --N 10")
run("main.py t1 gen tests/t1/variant.json --N abc")

section("## Задача 1.1. Режим 2 — точная вероятность и частотная оценка")
run("main.py t1 prob tests/t1/variant.json --N 10000 --seq ab --seed 1")
run("main.py t1 prob tests/t1/variant.json --N 10000 --seq aed --seed 1")
run("main.py t1 prob tests/t1/example2.json --N 10000 --seq 01 --seed 1")
run("main.py t1 prob tests/t1/ext_markov_ergodic.json --N 10000 --seq aa --seed 1")
for sd in (0, 1):
    run(f"main.py t1 prob tests/t1/ext_nonergodic_mixture.json --N 10000 --seq a --seed {sd}",
        "неэргодический источник: предел частоты зависит от реализации")
run("main.py t1 prob tests/t1/variant.json --N 0 --seq ab")
run("main.py t1 prob tests/t1/variant.json --N 100 --seq az --seed 1")

section("## Задача 1.2. Режим 1 — проверка и энтропия")
for f in ("t2/stationary", "t2/skewed", "t2/uniform5", "t1/degenerate_one_symbol",
          "t1/variant", "t1/ext_markov_ergodic", "t1/ext_nonergodic_mixture"):
    run(f"main.py t2 check tests/{f}.json")

section("## Задача 1.2. Режим 2 — равномерное кодирование")
run(f"main.py t2 code tests/t2/skewed.json --R 2 --out {OUT}/skewed_R2.code.json", "R > H")
run(f"main.py t2 code tests/t2/skewed.json --R 1.5 --out {OUT}/skewed_R1.5.code.json", "R < H")
run(f"main.py t2 code tests/t2/skewed.json --R 1.5 --eps 0.3 --nmax 20 --out {OUT}/c.json",
    "R < H, но при малом n условие выполнено")
run(f"main.py t2 code tests/t2/stationary.json --R 2.3 --out {OUT}/stationary.code.json",
    "R чуть больше H: n0 существует, но за пределами n_max = 50")
run(f"main.py t2 code tests/t2/uniform5.json --R 2.4 --nmax 5 --out {OUT}/c.json", "R > log2 k")
run(f"main.py t2 code tests/t1/degenerate_one_symbol.json --R 0 --nmax 3 --out {OUT}/c.json")
run("main.py t2 code tests/t1/variant.json --R 2")
run("main.py t2 code tests/t2/skewed.json --R -1")
run("main.py t2 code tests/t2/skewed.json --R 2 --q 1")

section("## Задача 1.3. Сжатие, --stats, восстановление")
files = [("text_ru.txt", "текст на русском"), ("text_en.txt", "текст на английском"),
         ("image.jpg", "изображение JPEG"), ("repeat.bin", "повтор одного байта"),
         ("empty.bin", "пустой файл"), ("two_bytes.bin", "два символа"),
         ("random.bin", "случайные байты")]
for f, what in files:
    src = f"tests/t3/{f}"
    if not os.path.exists(os.path.join(ROOT, src)):
        sections.append((f"(нет файла {src}: {what})", "", None, 0, None))
        continue
    run(f"main.py t3 compress {src} -o {OUT}/{f}.zmh --stats", what)
    run(f"main.py t3 decompress {OUT}/{f}.zmh -o {OUT}/{f}.out --force")
    with open(os.path.join(ROOT, src), "rb") as a, open(os.path.join(ROOT, OUT, f + ".out"), "rb") as b:
        same = a.read() == b.read()
    sections.append(("проверка", "восстановленный файл совпадает с исходным" if same
                      else "РАСХОЖДЕНИЕ", None, 0, None))

section("Диагностики повреждений:")
base = f"{OUT}/random.bin.zmh"
corrupt(base, f"{OUT}/trunc_data.zmh", lambda b: b[:-100])
corrupt(base, f"{OUT}/trunc_header.zmh", lambda b: b[:20])
corrupt(base, f"{OUT}/flip_data.zmh", lambda b: b[:len(b) // 2] + bytes([b[len(b) // 2] ^ 0x10]) + b[len(b) // 2 + 1:])
corrupt(base, f"{OUT}/flip_header.zmh", lambda b: b[:5] + bytes([b[5] ^ 1]) + b[6:])
corrupt(base, f"{OUT}/extra.zmh", lambda b: b + b"x")
run("main.py t3 decompress tests/t3/foreign.zmh -o tests/out/x --force", "чужой формат")
run(f"main.py t3 decompress {OUT}/trunc_data.zmh -o tests/out/x --force", "обрезан поток кодов")
run(f"main.py t3 decompress {OUT}/trunc_header.zmh -o tests/out/x --force", "обрезан заголовок")
run(f"main.py t3 decompress {OUT}/flip_data.zmh -o tests/out/x --force", "инверсия бита в середине данных")
run(f"main.py t3 decompress {OUT}/flip_header.zmh -o tests/out/x --force", "инверсия бита в заголовке")
run(f"main.py t3 decompress {OUT}/extra.zmh -o tests/out/x --force", "лишний байт в конце")
run("main.py t3 compress tests/t3/missing.bin")

with open(os.path.join(ROOT, "RESULTS.md"), "w", encoding="utf-8") as f:
    f.write("# RESULTS\n\nДословный вывод программы на собственных тестах. Файл создаётся "
            "скриптом `python3 run_tests.py`.\n")
    f.write(f"Python {sys.version.split()[0]}.\n\n")
    for s in sections:
        if isinstance(s, str):
            f.write(f"\n{s}\n\n")
            continue
        cmd, body, rc, dt, note = s
        if rc is None:
            f.write(f"*{cmd}*" + (f": {body}" if body else "") + "\n\n")
            continue
        if note:
            f.write(f"*{note}*\n\n")
        f.write("```\n" + cmd + "\n" + body + f"\n[код возврата {rc}, {dt:.2f} с]\n```\n\n")
bad = [s for s in sections if not isinstance(s, str) and s[2] not in (None, 0, 2)]
print(f"RESULTS.md записан; запусков: {sum(1 for s in sections if not isinstance(s, str) and s[2] is not None)}; "
      f"аварийных: {len(bad)}")
sys.exit(1 if bad else 0)
