import hashlib
import os
import struct
from typing import Dict, List

from src.constants import BYTEORDER_BIG

_SYLLABLES: List[str] = [
    "ba", "be", "bi", "bo", "bu", "ca", "ce", "ci", "co", "cu",
    "da", "de", "di", "do", "du", "fa", "fe", "fi", "fo", "fu",
    "ga", "ge", "gi", "go", "gu", "ha", "he", "hi", "ho", "hu",
    "ja", "je", "ji", "jo", "ju", "ka", "ke", "ki", "ko", "ku",
    "la", "le", "li", "lo", "lu", "ma", "me", "mi", "mo", "mu",
    "na", "ne", "ni", "no", "nu", "pa", "pe", "pi", "po", "pu",
    "ra", "re", "ri", "ro", "ru", "sa", "se", "si", "so", "su",
    "ta", "te", "ti", "to", "tu", "va", "ve", "vi", "vo", "vu",
    "za", "ze", "zi", "zo", "zu",
    "bra", "bre", "bri", "bro", "bru",
    "cra", "cre", "cri", "cro", "cru",
    "dra", "dre", "dri", "dro", "dru",
    "fra", "fre", "fri", "fro", "fru",
    "gra", "gre", "gri", "gro", "gru",
    "pra", "pre", "pri", "pro", "pru",
    "tra", "tre", "tri", "tro", "tru",
    "sta", "ste", "sti", "sto", "stu",
    "ska", "ske", "ski", "sko", "sku",
    "sla", "sle", "sli", "slo", "slu",
    "sna", "sne", "sni", "sno", "snu",
    "spa", "spe", "spi", "spo", "spu",
    "sma", "sme", "smi", "smo", "smu",
]

_N: int = len(_SYLLABLES)
_POSITIONS: int = 7
_NONCE_BITS: int = 16
_NONCE_MOD: int = 1 << _NONCE_BITS
_ROUNDS: int = 8
_HALF_LOW: int = _N ** (_POSITIONS // 2)
_HALF_HIGH: int = _N ** (_POSITIONS - _POSITIONS // 2)


def _round_key(key: bytes, r: int) -> bytes:
    return hashlib.blake2b(key + bytes([r]), digest_size=32).digest()


def _prf(rk: bytes, val: int, mod: int) -> int:
    digest = hashlib.blake2b(struct.pack(">Q", val), key=rk, digest_size=8).digest()
    return int.from_bytes(digest, BYTEORDER_BIG) % mod


def _feistel_encrypt(key: bytes, value: int) -> int:
    left: int = value // _HALF_LOW
    right: int = value % _HALF_LOW
    for r in range(_ROUNDS):
        mod = _HALF_HIGH if r % 2 == 0 else _HALF_LOW
        left, right = right, (left + _prf(_round_key(key, r), right, mod)) % mod
    return left * _HALF_LOW + right


def _feistel_decrypt(key: bytes, value: int) -> int:
    left: int = value // _HALF_LOW
    right: int = value % _HALF_LOW
    for r in range(_ROUNDS - 1, -1, -1):
        mod = _HALF_HIGH if r % 2 == 0 else _HALF_LOW
        left, right = (right - _prf(_round_key(key, r), left, mod)) % mod, left
    return left * _HALF_LOW + right


def _encode(value: int) -> str:
    parts: List[str] = []
    for _ in range(_POSITIONS):
        parts.append(_SYLLABLES[value % _N])
        value //= _N
    return "".join(parts)


def _decode(local: str) -> int:
    index: Dict[str, int] = {s: i for i, s in enumerate(_SYLLABLES)}
    value: int = 0
    multiplier: int = 1
    pos: int = 0
    while pos < len(local):
        matched = False
        for length in (3, 2):
            chunk = local[pos:pos + length]
            if chunk in index:
                value += index[chunk] * multiplier
                multiplier *= _N
                pos += length
                matched = True
                break
        if not matched:
            raise ValueError(local)
    return value


def generate_local(key: bytes, user_id: int, nonce: int) -> str:
    inp = user_id * _NONCE_MOD + nonce
    return _encode(_feistel_encrypt(key, inp))


def random_nonce() -> int:
    return int.from_bytes(os.urandom(2), BYTEORDER_BIG)


def belongs_to_user(key: bytes, user_id: int, local: str) -> bool:
    try:
        target = _feistel_decrypt(key, _decode(local))
    except ValueError:
        return False
    return target // _NONCE_MOD == user_id
