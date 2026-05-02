
import hashlib
import secrets


def mask_address(address: str) -> str:
    if not address:
        return ''
    if len(address) <= 12:
        return address[0:3] + '...' + address[-3:]
    return address[:6] + '...' + address[-6:]


def mask_personal(name: str, phone: str = '') -> str:
    n = name or ''
    masked_name = n[0] + '***' + n[-1] if len(n) > 2 else n
    if phone:
        masked_phone = phone[:2] + '*****' + phone[-2:]
        return f"{masked_name} ({masked_phone})"
    return masked_name


def obfuscate_reference(ref: str) -> str:
    salt = secrets.token_hex(8)
    digest = hashlib.sha256((salt + (ref or '')).encode('utf-8')).hexdigest()
    return digest