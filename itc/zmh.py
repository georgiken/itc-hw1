"""Задача 1.3: контейнер zmh, двухпроходное сжатие Хаффманом и восстановление.

Формат (все числа big-endian):
  0   4  сигнатура  b"ZMH\\x01" (последний байт — версия)
  4   8  длина исходного файла N, байт
  12  4  CRC-32 исходных данных
  16  8  длина потока кодов в битах B
  24  1  способ хранения модели: 0 — список пар, 1 — таблица на 256 байт
  25  .  модель:
           способ 0: m (1 байт, 0..127), затем m пар (байт, длина кода)
           способ 1: 256 байт — длина кода для каждого значения байта (0 — нет)
  .   4  CRC-32 всех предыдущих байт заголовка
  .   .  поток кодов: ceil(B/8) байт, биты от старшего к младшему,
         неполный последний байт добивается нулями
Модель — длины канонического кода Хаффмана, по ним коды восстанавливаются однозначно.
"""
import struct

from .crc32 import crc32
from .errors import InputError
from .huffman import code_lengths, canonical_codes, kraft_ok, Decoder

MAGIC = b"ZMH\x01"
CHUNK = 1 << 16
_FIXED = struct.Struct(">4sQIQB")  # 25 байт


class ZmhError(InputError):
    kind = "повреждён"

    def __init__(self, msg):
        super().__init__(f"{self.kind}: {msg}")


class Foreign(ZmhError):
    kind = "чужой формат"


class Truncated(ZmhError):
    kind = "файл обрезан"


class Corrupted(ZmhError):
    kind = "файл повреждён"


def _read(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        raise InputError(f"файл не найден: {path}") from None
    except IsADirectoryError:
        raise InputError(f"{path}: это каталог") from None
    except OSError as e:
        raise InputError(f"{path}: {e.strerror}") from None


def count_freqs(path):
    """Первый проход: частоты байтов (чтение блоками)."""
    freqs = [0] * 256
    crc, n = 0, 0
    try:
        with open(path, "rb") as f:
            while True:
                block = f.read(CHUNK)
                if not block:
                    break
                for b in block:
                    freqs[b] += 1
                crc = crc32(block, crc)
                n += len(block)
    except FileNotFoundError:
        raise InputError(f"файл не найден: {path}") from None
    except IsADirectoryError:
        raise InputError(f"{path}: это каталог") from None
    except OSError as e:
        raise InputError(f"{path}: {e.strerror}") from None
    return {b: f for b, f in enumerate(freqs) if f}, n, crc


def encode_model(lengths):
    m = len(lengths)
    if m <= 127:
        body = bytes([m]) + b"".join(bytes([s, l]) for s, l in sorted(lengths.items()))
        return 0, body
    table = bytearray(256)
    for s, l in lengths.items():
        table[s] = l
    return 1, bytes(table)


def build_header(n, crc, bits, lengths):
    mode, body = encode_model(lengths)
    head = _FIXED.pack(MAGIC, n, crc, bits, mode) + body
    return head + struct.pack(">I", crc32(head))


def compress(src_path, dst_path):
    freqs, n, crc = count_freqs(src_path)             # проход 1: модель
    lengths = code_lengths(freqs)
    codes = canonical_codes(lengths)
    bits = sum(f * lengths[s] for s, f in freqs.items())
    header = build_header(n, crc, bits, lengths)
    table = [codes.get(b, (0, 0)) for b in range(256)]
    out = bytearray()
    acc, nacc = 0, 0
    with open(src_path, "rb") as f:                   # проход 2: кодирование
        while True:
            block = f.read(CHUNK)
            if not block:
                break
            for b in block:
                c, l = table[b]
                acc = (acc << l) | c
                nacc += l
                if nacc >= 8:
                    while nacc >= 8:
                        nacc -= 8
                        out.append((acc >> nacc) & 0xFF)
                    acc &= (1 << nacc) - 1
    if nacc:  # неполный последний байт — добиваем нулями
        out.append((acc << (8 - nacc)) & 0xFF)
    try:
        with open(dst_path, "wb") as f:
            f.write(header)
            f.write(out)
    except OSError as e:
        raise InputError(f"не удалось записать {dst_path}: {e.strerror}") from None
    return {"freqs": freqs, "n": n, "lengths": lengths, "header": len(header),
            "data": len(out), "bits": bits}


def parse_header(blob):
    if len(blob) < len(MAGIC):
        if MAGIC.startswith(blob) and blob:
            raise Truncated("заголовок неполный")
        raise Foreign("нет сигнатуры zmh")
    if blob[:3] != MAGIC[:3]:
        raise Foreign("нет сигнатуры zmh")
    if blob[3] != MAGIC[3]:
        raise Foreign(f"неподдерживаемая версия формата {blob[3]}")
    if len(blob) < _FIXED.size + 1:
        raise Truncated("заголовок неполный")
    _, n, crc, bits, mode = _FIXED.unpack_from(blob)
    pos = _FIXED.size
    if mode == 0:
        m = blob[pos]
        need = pos + 1 + 2 * m + 4
        if m > 127:
            raise Corrupted("некорректный размер модели")
        if len(blob) < need:
            raise Truncated("заголовок неполный")
        pairs = blob[pos + 1: pos + 1 + 2 * m]
        lengths = {pairs[2 * i]: pairs[2 * i + 1] for i in range(m)}
        if len(lengths) != m:
            raise Corrupted("в модели повторяется символ")
        pos += 1 + 2 * m
    elif mode == 1:
        if len(blob) < pos + 256 + 4:
            raise Truncated("заголовок неполный")
        lengths = {s: l for s, l in enumerate(blob[pos: pos + 256]) if l}
        pos += 256
    else:
        raise Corrupted(f"неизвестный способ хранения модели {mode}")
    (hcrc,) = struct.unpack_from(">I", blob, pos)
    if crc32(blob[:pos]) != hcrc:
        raise Corrupted("не совпала контрольная сумма заголовка")
    pos += 4
    if n and not kraft_ok(lengths):
        raise Corrupted("длины кодов не образуют полный префиксный код")
    if not n and lengths:
        raise Corrupted("модель у пустого файла")
    return {"n": n, "crc": crc, "bits": bits, "lengths": lengths, "header": pos}


def decompress(src_path, dst_path):
    blob = _read(src_path)
    h = parse_header(blob)
    data = memoryview(blob)[h["header"]:]
    need = (h["bits"] + 7) // 8
    if len(data) < need:
        raise Truncated(f"поток кодов: {len(data)} байт из {need}")
    if len(data) > need:
        raise Corrupted(f"лишние {len(data) - need} байт после потока кодов")
    n, lengths = h["n"], h["lengths"]
    out = bytearray()
    if n and len(lengths) == 1:  # один символ: код длины 0, данных нет
        if h["bits"]:
            raise Corrupted("для одного символа поток кодов должен быть пустым")
        out = bytearray([next(iter(lengths))]) * n
    elif n:
        dec = Decoder(lengths)
        first, count, offset, syms = dec.first, dec.count, dec.offset, dec.syms
        code = l = 0
        used = 0
        total = h["bits"]
        for byte in data:
            for k in range(7, -1, -1):
                if used == total:
                    break
                code = (code << 1) | ((byte >> k) & 1)
                l += 1
                used += 1
                idx = code - first[l]
                if idx < count[l]:
                    out.append(syms[offset[l] + idx])
                    code = l = 0
            if used == total:
                break
        if l:
            raise Corrupted("поток кодов оборвался посреди кодового слова")
        if len(out) != n:
            raise Corrupted(f"декодировано {len(out)} байт вместо {n}")
        tail = h["bits"] % 8
        if tail and data[-1] & ((1 << (8 - tail)) - 1):
            raise Corrupted("ненулевые биты добивки в последнем байте")
    elif h["bits"]:
        raise Corrupted("поток кодов у пустого файла")
    if crc32(out) != h["crc"]:
        raise Corrupted("не совпала контрольная сумма восстановленных данных")
    try:
        with open(dst_path, "wb") as f:
            f.write(out)
    except OSError as e:
        raise InputError(f"не удалось записать {dst_path}: {e.strerror}") from None
    return h
