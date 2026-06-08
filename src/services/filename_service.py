import re
from typing import Optional

_FORBIDDEN_CHARS: str = r'[\\/:*?"<>|\x00-\x1f\x7f]'
_TRAILING_INVALID: str = r'[\s.]+$'
_EXT: str = ".html"
_FALLBACK: str = "letter"
_MAX_STEM_LEN: int = 255 - len(_EXT)


def _sanitize(name: str) -> Optional[str]:
    cleaned = re.sub(_FORBIDDEN_CHARS, "_", name)
    cleaned = re.sub(_TRAILING_INVALID, "", cleaned).strip()
    if not cleaned:
        return None
    return cleaned[:_MAX_STEM_LEN]


def make_filename(subject: Optional[str], sender: str) -> str:
    if subject is not None:
        stem = _sanitize(subject)
        if stem is not None:
            return stem + _EXT

    stem = _sanitize(sender)
    if stem is not None:
        return stem + _EXT

    return _FALLBACK + _EXT
