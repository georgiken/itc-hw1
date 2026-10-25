# --- начало сгенерированного фрагмента DeepSeek ---

_TABLE = []
for _n in range(256):
    _c = _n
    for _ in range(8):
        _c = (_c >> 1) ^ 0xEDB88320 if _c & 1 else _c >> 1
    _TABLE.append(_c)
# --- конец сгенерированного фрагмента ---

def crc32(data: bytes, crc: int = 0) -> int:
    crc ^= 0xFFFFFFFF
    t = _TABLE
    for b in data:
        crc = t[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return crc ^ 0xFFFFFFFF
