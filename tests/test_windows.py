import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import threading
import time
from PIL import Image

from creator.builder import compiler_path, doctor, run_tool
from creator.config import ROOT, SDK
from creator.validation import password_record
from creator.icons import normalize_icon


@contextmanager
def browser_workdir():
    work_root = (ROOT / 'work').resolve()
    directory = Path(tempfile.mkdtemp(dir=work_root, prefix='browser-test-')).resolve()
    assert directory.is_relative_to(work_root)
    try:
        yield directory
    finally:
        # WebView2 renderer jarayoni chiqishda profil fayllarini biroz kechroq bo'shatadi.
        for attempt in range(30):
            try:
                shutil.rmtree(directory)
                break
            except OSError:
                if attempt == 29:
                    raise
                time.sleep(0.2)


@unittest.skipUnless(os.name == 'nt' and not doctor(), 'Windows yig\'ish vositalari kerak')
class WindowsIntegrationTests(unittest.TestCase):
    def test_real_dotnet_password_and_close_dialog(self):
        work_root = ROOT / 'work'
        work_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work_root, prefix='test-') as directory:
            work = Path(directory)
            config = work / 'test.json'
            config.write_text(json.dumps({'Name': 'Test', 'Url': 'https://example.com/',
                                          'Id': 'INTEGRATION-TEST', 'Password': password_record('salom🔒123')}), encoding='utf-8')
            executable = work / 'IntegrationTests.exe'
            core = SDK / 'lib/net462/Microsoft.Web.WebView2.Core.dll'
            forms = SDK / 'lib/net462/Microsoft.Web.WebView2.WinForms.dll'
            run_tool([str(compiler_path()), '/nologo', '/target:exe', '/platform:x64', '/utf8output',
                      '/codepage:65001', '/main:IntegrationTests', '/out:' + str(executable),
                      '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
                      '/reference:System.Web.Extensions.dll', '/reference:' + str(core), '/reference:' + str(forms),
                      str(ROOT / 'windows/Program.cs'), str(ROOT / 'windows/ExitProtection.cs'),
                      str(ROOT / 'windows/Theme.cs'),
                      str(ROOT / 'tests/WindowsHarness.cs')], work)
            for source in (core, forms, SDK / 'runtimes/win-x64/native/WebView2Loader.dll'):
                shutil.copy2(source, work / source.name)
            result = subprocess.run([str(executable), str(config)], capture_output=True, timeout=90)
            self.assertEqual(result.returncode, 0, (result.stdout + result.stderr).decode(errors='replace'))
            self.assertIn(b'ALL WINDOWS CHECKS PASSED', result.stdout)

    def test_live_webview_theme_changes_and_embedded_icon(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                data = b'<!doctype html><html><head><meta charset="utf-8"><title>Theme Test</title></head><body style="margin:0;background:#101214;color:white;min-height:100vh">Theme Test</body></html>'
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
            threading.Thread(target=server.serve_forever, daemon=True).start()
            try:
                self.run_browser_harness(f'http://127.0.0.1:{server.server_port}/')
            finally:
                server.shutdown()

    def run_browser_harness(self, url):
        work_root = ROOT / 'work'
        work_root.mkdir(exist_ok=True)
        with browser_workdir() as directory:
            work = Path(directory)
            config = work / 'test.json'
            config.write_text(json.dumps({'Name': 'Theme Test', 'Url': url, 'Id': 'THEME-TEST', 'Password': None}), encoding='utf-8')
            image = BytesIO()
            Image.new('RGBA', (256, 256), '#33cc99').save(image, format='PNG')
            icon = work / 'test.ico'
            icon.write_bytes(normalize_icon(image.getvalue()))
            executable = work / 'BrowserTests.exe'
            core = SDK / 'lib/net462/Microsoft.Web.WebView2.Core.dll'
            forms = SDK / 'lib/net462/Microsoft.Web.WebView2.WinForms.dll'
            run_tool([str(compiler_path()), '/nologo', '/target:exe', '/platform:x64', '/utf8output',
                      '/codepage:65001', '/main:BrowserTests', '/out:' + str(executable),
                      '/resource:' + str(ROOT / 'windows/theme.js') + ',theme.js',
                      '/resource:' + str(icon) + ',app.ico', '/win32icon:' + str(icon),
                      '/reference:System.Windows.Forms.dll', '/reference:System.Drawing.dll',
                      '/reference:System.Web.Extensions.dll', '/reference:' + str(core), '/reference:' + str(forms),
                      str(ROOT / 'windows/Program.cs'), str(ROOT / 'windows/ExitProtection.cs'),
                      str(ROOT / 'windows/Theme.cs'), str(ROOT / 'tests/BrowserHarness.cs')], work)
            for source in (core, forms, SDK / 'runtimes/win-x64/native/WebView2Loader.dll'):
                shutil.copy2(source, work / source.name)
            env = dict(os.environ, WEBVIEW2_USER_DATA_FOLDER=str(work / 'browser-profile'))
            result = subprocess.run([str(executable), str(config)], capture_output=True, timeout=90, env=env)
            self.assertEqual(result.returncode, 0, (result.stdout + result.stderr).decode(errors='replace'))
            self.assertIn(b'ALL BROWSER CHECKS PASSED', result.stdout)
