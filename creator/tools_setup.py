"""Rasmiy manbalardan lokal yig'ish vositalarini tayyorlash."""
from pathlib import Path
import shutil
import subprocess
import urllib.request
import zipfile

from .config import BOOTSTRAPPER, ISCC, SDK, SDK_VERSION, TOOLS

INNO_URL = 'https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe'
WEBVIEW_URL = f'https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/{SDK_VERSION}/microsoft.web.webview2.{SDK_VERSION}.nupkg'
BOOTSTRAPPER_URL = 'https://go.microsoft.com/fwlink/p/?LinkId=2124703'


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + '.part')
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'ExeCreator-Setup/1.0'})
        with urllib.request.urlopen(request, timeout=120) as response, partial.open('wb') as out:
            shutil.copyfileobj(response, out)
        partial.replace(target)
    finally:
        partial.unlink(missing_ok=True)


def verify_signature(path: Path, publisher: str) -> None:
    # Yo'lni shell kodiga qo'shmaymiz: $args orqali uzatiladi.
    script = TOOLS / 'verify-signature.ps1'
    script.write_text(
        'param([string]$Target, [string]$Publisher)\n'
        '$ErrorActionPreference = "Stop"\n'
        'Import-Module (Join-Path $PSHOME "Modules\\Microsoft.PowerShell.Security\\Microsoft.PowerShell.Security.psd1")\n'
        '$signature = Get-AuthenticodeSignature -LiteralPath $Target\n'
        'if ($signature.Status -ne "Valid" -or $signature.SignerCertificate.Subject -notlike "*$Publisher*") '
        '{ throw "Yuklangan faylning rasmiy raqamli imzosi tasdiqlanmadi." }\n', encoding='utf-8-sig')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                             str(script), '-Target', str(path), '-Publisher', publisher],
                            capture_output=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError('Raqamli imzo tekshiruvi: ' + (result.stdout + result.stderr).decode(errors='replace'))


def main() -> None:
    TOOLS.mkdir(exist_ok=True)
    if not (SDK / 'lib/net462/Microsoft.Web.WebView2.WinForms.dll').is_file():
        print('1/3 Microsoft WebView2 SDK yuklanmoqda…', flush=True)
        archive = TOOLS / ('webview2-' + SDK_VERSION + '.nupkg')
        download(WEBVIEW_URL, archive)
        with zipfile.ZipFile(archive) as package:
            for member in package.namelist():
                if (member.startswith('lib/net462/') or member.startswith('runtimes/win-x64/native/')
                        or ('/' not in member and 'LICENSE' in member.upper())):
                    # Zip yo'li loyiha SDK papkasidan chiqmasin.
                    dest = (SDK / member).resolve()
                    if not dest.is_relative_to(SDK.resolve()):
                        raise RuntimeError('SDK arxivida noto\'g\'ri yo\'l.')
                    package.extract(member, SDK)
    else:
        print('1/3 WebView2 SDK mavjud.', flush=True)
    if not BOOTSTRAPPER.is_file():
        print('2/3 Microsoft WebView2 o\'rnatuvchisi yuklanmoqda…', flush=True)
        download(BOOTSTRAPPER_URL, BOOTSTRAPPER)
    verify_signature(BOOTSTRAPPER, 'Microsoft Corporation')
    if not ISCC.is_file():
        print('3/3 Inno Setup yuklanmoqda va loyiha ichiga o\'rnatilmoqda…', flush=True)
        setup = TOOLS / 'innosetup-6.7.3.exe'
        download(INNO_URL, setup)
        verify_signature(setup, 'Pyrsys B.V.')
        subprocess.run([str(setup), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-',
                        '/CURRENTUSER', '/DIR=' + str(ISCC.parent), '/NOICONS', '/TASKS='],
                       check=True, timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    if not ISCC.is_file():
        raise RuntimeError('Inno Setup kompilyatori topilmadi.')
    print('Tayyor. python -m creator.builder --doctor orqali tekshiring.', flush=True)


if __name__ == '__main__':
    main()
