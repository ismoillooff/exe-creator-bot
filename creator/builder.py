import argparse
from dataclasses import dataclass
from getpass import getpass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid
from dotenv import load_dotenv

from .config import BOOTSTRAPPER, ISCC, MAX_DOCUMENT_BYTES, ROOT, SDK
from .validation import normalize_url, password_record, validate_name
from .icons import default_icon, normalize_icon
from .signing import SigningError, sign_and_verify, signing_config


class BuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class BuildSpec:
    url: str
    name: str
    password: dict | None
    icon: bytes | None = None


def compiler_path() -> Path:
    return Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'


def doctor() -> list[str]:
    errors = []
    if os.name != 'nt':
        errors.append('EXE yig\'ish Windows x64 kompyuterida bajariladi.')
    if not compiler_path().is_file():
        errors.append('.NET Framework 4.8 C# kompilyatori topilmadi.')
    if os.name == 'nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full') as key:
                if winreg.QueryValueEx(key, 'Release')[0] < 528040:
                    errors.append('.NET Framework 4.8 yoki yangiroq versiyasi kerak.')
        except OSError:
            errors.append('.NET Framework 4.8 o\'rnatilmagan.')
    for path in (ISCC, BOOTSTRAPPER, SDK / 'lib/net462/Microsoft.Web.WebView2.Core.dll',
                 SDK / 'lib/net462/Microsoft.Web.WebView2.WinForms.dll',
                 SDK / 'runtimes/win-x64/native/WebView2Loader.dll'):
        if not path.is_file():
            errors.append(f'Yetishmaydi: {path.relative_to(ROOT)}; setup.bat ni ishga tushiring.')
    try:
        signing_config()
    except SigningError as error:
        errors.append(str(error))
    return errors


def run_tool(args: list[str], cwd: Path, timeout: int = 240) -> None:
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        raise BuildError('Yig\'ish vaqti tugadi. Qayta urinib ko\'ring.') from None
    if result.returncode:
        # Bu yerda token, xom parol yoki foydalanuvchi xabarlari mavjud emas.
        output = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        raise BuildError(f'Kompilyator xatosi:\n{output[-4000:]}')


def iss_value(value: str | Path) -> str:
    return str(value).replace('{', '{{').replace('"', '""')


def build_installer(spec: BuildSpec, output_dir: Path | None = None) -> Path:
    url, name = normalize_url(spec.url), validate_name(spec.name)
    errors = doctor()
    if errors:
        raise BuildError('\n'.join(errors))
    signer = signing_config()
    app_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url + '\n' + name)).upper()
    job_id = uuid.uuid4().hex
    output_dir = (output_dir or ROOT / 'dist' / job_id).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    work_root = ROOT / 'work'
    work_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='build-', dir=work_root) as temp:
        work = Path(temp)
        payload = work / 'payload'
        payload.mkdir()
        icon_file = payload / 'app.ico'
        icon_file.write_bytes(normalize_icon(spec.icon) if spec.icon else default_icon())
        config = {'Name': name, 'Url': url, 'Id': app_id, 'Password': spec.password}
        config_file = work / 'app.json'
        config_file.write_text(json.dumps(config, ensure_ascii=True), encoding='utf-8')
        executable = payload / (name + '.exe')
        core = SDK / 'lib/net462/Microsoft.Web.WebView2.Core.dll'
        forms = SDK / 'lib/net462/Microsoft.Web.WebView2.WinForms.dll'
        run_tool([str(compiler_path()), '/nologo', '/target:winexe', '/platform:x64', '/optimize+',
                  '/utf8output', '/codepage:65001', '/out:' + str(executable),
                  '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
                  '/reference:System.Web.Extensions.dll', '/reference:System.Net.Http.dll',
                  '/reference:' + str(core), '/reference:' + str(forms),
                  '/resource:' + str(config_file) + ',app.json',
                  '/resource:' + str(icon_file) + ',app.ico',
                  '/resource:' + str(ROOT / 'windows/theme.js') + ',theme.js',
                  '/win32icon:' + str(icon_file),
                  '/win32manifest:' + str(ROOT / 'windows/app.manifest'),
                  str(ROOT / 'windows/Program.cs'), str(ROOT / 'windows/ExitProtection.cs'),
                  str(ROOT / 'windows/Theme.cs')], work)
        if signer:
            try:
                sign_and_verify(executable, signer)
            except SigningError as error:
                raise BuildError(str(error)) from error
        for dll in (core, forms, SDK / 'runtimes/win-x64/native/WebView2Loader.dll'):
            shutil.copy2(dll, payload / dll.name)
        shutil.copy2(ROOT / 'windows/App.config', payload / (name + '.exe.config'))
        notice = payload / 'THIRD-PARTY-NOTICES.txt'
        notice.write_text('Microsoft WebView2 SDK\nhttps://www.nuget.org/packages/Microsoft.Web.WebView2/\n\n', encoding='utf-8')
        for license_path in SDK.glob('*LICENSE*'):
            with notice.open('a', encoding='utf-8') as target:
                target.write(license_path.read_text(encoding='utf-8-sig') + '\n')
        template = (ROOT / 'windows/installer.iss').read_text(encoding='utf-8')
        values = {'APP_ID': app_id, 'APP_NAME': name, 'PAYLOAD': str(payload),
                  'BOOTSTRAPPER': str(BOOTSTRAPPER), 'OUTPUT': str(output_dir)}
        for key, value in values.items():
            template = template.replace('@@' + key + '@@', iss_value(value))
        script = work / 'installer.iss'
        script.write_text(template, encoding='utf-8-sig')
        run_tool([str(ISCC), '/Qp', str(script)], work)
    installer = output_dir / (name + '-Setup.exe')
    if not installer.is_file():
        raise BuildError('O\'rnatuvchi fayl yaratilmagan.')
    if signer:
        try:
            sign_and_verify(installer, signer)
        except SigningError as error:
            # Imzolash so'ralganida imzosiz natija yuborishga o'tilmaydi.
            raise BuildError(str(error)) from error
    if installer.stat().st_size > MAX_DOCUMENT_BYTES:
        raise BuildError('Fayl Telegram yuborish limitidan katta. dist papkasidan qo\'lda oling.')
    with installer.open('rb') as file:
        digest = hashlib.file_digest(file, 'sha256').hexdigest()
    (output_dir / 'SHA256.txt').write_text(digest + '  ' + installer.name + '\n', encoding='utf-8')
    metadata = {'app_signed': signer is not None, 'installer_signed': signer is not None,
                'authenticode_verified': signer is not None, 'sha256': digest,
                'filename': installer.name, 'installer_version': '1.2.1'}
    (output_dir / 'BUILD-INFO.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    return installer


def main() -> None:
    load_dotenv(ROOT / '.env')
    parser = argparse.ArgumentParser(description='Sayt uchun Windows o\'rnatuvchisini yarating.')
    parser.add_argument('--doctor', action='store_true')
    parser.add_argument('--url')
    parser.add_argument('--name')
    parser.add_argument('--icon', type=Path, help='PNG/JPG/WEBP/BMP/ICO rasm; berilmasa standart ikonka')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--ask-password', action='store_true')
    group.add_argument('--no-password', action='store_true')
    args = parser.parse_args()
    if args.doctor:
        errors = doctor()
        print('\n'.join(errors) if errors else 'Tayyor: kompilyator, WebView2 SDK va Inno Setup mavjud.')
        raise SystemExit(bool(errors))
    if not args.url or not args.name or not (args.ask_password or args.no_password):
        parser.error('--url, --name va --ask-password yoki --no-password kerak.')
    try:
        password = getpass('Chiqish paroli: ') if args.ask_password else None
        if password is not None and password != getpass('Parolni takrorlang: '):
            parser.error('Parollar mos kelmadi.')
        record = password_record(password)
        del password
        icon = args.icon.read_bytes() if args.icon else None
        path = build_installer(BuildSpec(args.url, args.name, record, icon))
        print(f'Tayyor: {path}')
    except (ValueError, BuildError, OSError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
