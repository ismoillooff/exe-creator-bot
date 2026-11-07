import base64
import hashlib
import re
import secrets
from urllib.parse import urlsplit, urlunsplit

from .config import PBKDF2_ITERATIONS


def normalize_url(value: str) -> str:
    value = value.strip()
    if not value or len(value) > 2048 or any(c.isspace() or ord(c) < 32 for c in value):
        raise ValueError("To'g'ri sayt havolasini kiriting (2048 belgigacha).")
    if '://' not in value:
        value = 'https://' + value
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in ('http', 'https') or not parsed.hostname:
            raise ValueError()
        if parsed.username is not None or parsed.password is not None or '\\' in value:
            raise ValueError()
        parsed.port  # Noto'g'ri portlar ham rad etiladi.
        host = parsed.hostname
        # IDN domenlarini .NET va brauzerga mos ASCII ko'rinishiga o'tkazish.
        if ':' in host:
            import ipaddress
            ipaddress.IPv6Address(host)
            host = '[' + host + ']'
        else:
            host = host.encode('idna').decode('ascii')
            if not all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', label)
                       for label in host.rstrip('.').split('.')):
                raise ValueError()
        if parsed.port is not None:
            host += ':' + str(parsed.port)
        return urlunsplit((parsed.scheme.lower(), host, parsed.path or '/', parsed.query, parsed.fragment))
    except (ValueError, UnicodeError):
        raise ValueError("Faqat http:// yoki https:// sayt havolasini kiriting. Login/parol URL ichida bo'lmasin.") from None


def validate_name(value: str) -> str:
    name = value.strip()
    if name.lower().endswith('.exe'):
        name = name[:-4]
    if not 1 <= len(name) <= 60 or name.endswith(('.', ' ')):
        raise ValueError('Dastur nomi 1–60 belgi bo\'lsin; oxiri nuqta yoki bo\'shliq bo\'lmasin.')
    if re.search(r'[<>:"/\\|?*{}\x00-\x1f\x7f]', name):
        raise ValueError('Nomda quyidagi belgilar mumkin emas: < > : " / \\ | ? * { }')
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'CLOCK$', 'CONIN$', 'CONOUT$'}
    reserved.update(f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in (*range(1, 10), '¹', '²', '³'))
    if name.split('.')[0].upper() in reserved or name in ('.', '..'):
        raise ValueError('Bu nom Windows tomonidan band qilingan. Boshqa nom kiriting.')
    return name


def password_record(password: str | None) -> dict | None:
    if password is None:
        return None
    # Paroldagi bo'shliqlar saqlanadi; Telegram va .NET bir xil UTF-8 ishlatadi.
    if not 4 <= len(password) <= 128:
        raise ValueError("Parol 4–128 belgidan iborat bo'lsin.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    return {'Salt': base64.b64encode(salt).decode(), 'Hash': base64.b64encode(digest).decode(),
            'Iterations': PBKDF2_ITERATIONS}
