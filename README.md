# ДЗ №1. Кодирование источников

Python ≥ 3.10 (проверено на 3.10 и 3.13), только стандартная библиотека.
Все режимы неинтерактивны; случайность управляется `--seed`.
Некорректный вход — сообщение в stderr и код возврата 2.

```
python3 main.py --variant

# 1.1 Моделирование источника (исходный и расширенный формат, см. SPEC.md)
python3 main.py t1 gen  FILE.json [--N N|None] [--seed S]      # режим 1; без N — до Ctrl+C
python3 main.py t1 prob FILE.json --N N --seq SEQ [--seed S]    # режим 2; SEQ = "ab" или "a,b"

# 1.2 Равномерное кодирование источника без памяти
python3 main.py t2 check FILE.json                               # режим 1
python3 main.py t2 code  FILE.json --R R [--eps E] [--q Q] [--nmax 50] [--out CODE.json]

# 1.3 Архиватор zmh
python3 main.py t3 compress   FILE [-o FILE.zmh] [--stats]
python3 main.py t3 decompress FILE.zmh [-o FILE] [--force]

# все тесты -> RESULTS.md
python3 run_tests.py
```

Документы: `REPORT.md` — отчёт, `SPEC.md` — расширенный формат,
`RESULTS.md` — вывод программы на тестах, `SOURCES.md` — источники.
