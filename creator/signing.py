"""Windows certificate store orqali ixtiyoriy Authenticode imzolash.

Sertifikat va uning private key'i operator tomonidan oldindan o'rnatiladi.
Modul sertifikat yaratmaydi yoki Windows ishonch sozlamalarini o'zgartirmaydi.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit


class SigningError(RuntimeError):
    pass


@dataclass(frozen=True)
class SigningConfig:
    tool: Path
    thumbprint: str
    machine_store: bool
    timestamp_url: str


def find_signtool() -> Path | None:
    explicit = os.getenv('SIGNTOOL_PATH', '').strip()
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            raise SigningError('SIGNTOOL_PATH mavjud signtool.exe fayliga yo\'naltirilishi kerak.')
        return path.resolve()
    found = shutil.which('signtool.exe')
    if found:
        return Path(found)
    sdk_bin = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Windows Kits/10/bin'
    candidates = list(sdk_bin.glob('*/x64/signtool.exe'))
    def version(path):
        return tuple(int(part) if part.isdigit() else 0 for part in path.parents[1].name.split('.'))
    return max(candidates, key=version) if candidates else None


def signing_config() -> SigningConfig | None:
    required = os.getenv('REQUIRE_SIGNED_BUILDS', '0').strip().lower()
    if required not in ('0', '1', 'true', 'false'):
        raise SigningError('REQUIRE_SIGNED_BUILDS qiymati 0 yoki 1 bo\'lsin.')
    thumbprint = re.sub(r'\s+', '', os.getenv('SIGN_CERT_SHA1', '')).upper()
    if not thumbprint:
        if required in ('1', 'true'):
            raise SigningError('Imzolangan EXE talab qilinmoqda. SIGN_CERT_SHA1 va ishonchli code-signing sertifikati kerak.')
        return None
    if not re.fullmatch(r'[0-9A-F]{40}', thumbprint):
        raise SigningError('SIGN_CERT_SHA1 sertifikatning 40 ta hex belgili thumbprint qiymati bo\'lishi kerak.')
    store = os.getenv('SIGN_CERT_STORE', 'CurrentUser').strip()
    if store.lower() not in ('currentuser', 'localmachine'):
        raise SigningError('SIGN_CERT_STORE: CurrentUser yoki LocalMachine bo\'lsin.')
    timestamp = os.getenv('SIGN_TIMESTAMP_URL', 'http://timestamp.digicert.com').strip()
    try:
        parsed = urlsplit(timestamp)
        if (parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or any(c.isspace() for c in timestamp)):
            raise ValueError()
        parsed.port
    except ValueError:
        raise SigningError('SIGN_TIMESTAMP_URL to\'g\'ri http/https RFC3161 timestamp manzili bo\'lishi kerak.') from None
    tool = find_signtool()
    if tool is None:
        raise SigningError('SignTool topilmadi. Windows SDK Signing Tools o\'rnating yoki SIGNTOOL_PATH ni belgilang.')
    return SigningConfig(tool, thumbprint, store.lower() == 'localmachine', timestamp)


def _run(args: list[str]) -> None:
    try:
        result = subprocess.run(args, capture_output=True, timeout=180,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SigningError('SignTool bajarilmadi. Vosita, sertifikat/private key, token/HSM va timestamp ulanishini tekshiring.') from error
    if result.returncode:
        details = (result.stdout + result.stderr).decode(errors='replace')[-2000:]
        raise SigningError('EXE imzolash yoki imzoni tekshirish muvaffaqiyatsiz.\n' + details)


def sign_and_verify(path: Path, config: SigningConfig) -> None:
    args = [str(config.tool), 'sign', '/sha1', config.thumbprint, '/s', 'My',
            '/fd', 'SHA256', '/tr', config.timestamp_url, '/td', 'SHA256']
    if config.machine_store:
        args.append('/sm')
    args.append(str(path.resolve()))
    _run(args)
    # Self-signed yoki ishonchsiz zanjir bilan muvaffaqiyatli natija deb e'lon qilinmaydi.
    _run([str(config.tool), 'verify', '/pa', '/all', '/tw', str(path.resolve())])
