from emval import validate_email

from src.constants import AT_SIGN


def normalize_address(raw: str, domain: str) -> str:
    text = raw.strip()
    address = text if AT_SIGN in text else text + AT_SIGN + domain

    try:
        normalized: str = validate_email(address, deliverable_address=False).normalized
    except SyntaxError:
        raise

    addr_domain = normalized.split(AT_SIGN, 1)[1].lower()
    if addr_domain != domain:
        raise SyntaxError(addr_domain)

    return normalized
