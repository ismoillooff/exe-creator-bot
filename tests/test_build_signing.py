import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from creator.builder import BuildError, BuildSpec, build_installer
from creator.config import ROOT
from creator.signing import SigningConfig, SigningError


class BuildSigningTests(unittest.TestCase):
    def exercise(self, signer, fail_on=None):
        events = []
        (ROOT / 'work').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'work', prefix='signing-test-') as directory:
            output = Path(directory)

            def tool(args, cwd):
                out = next((arg[5:] for arg in args if arg.startswith('/out:')), None)
                if out:
                    events.append('compile')
                    Path(out).write_bytes(b'MZ-test-app')
                else:
                    events.append('package')
                    (output / 'Test App-Setup.exe').write_bytes(b'MZ-test-installer')

            def sign(path, config):
                event = 'sign-installer' if path.name.endswith('-Setup.exe') else 'sign-app'
                events.append(event)
                if event == fail_on:
                    raise SigningError('Expected test failure')

            with patch('creator.builder.doctor', return_value=[]), \
                 patch('creator.builder.signing_config', return_value=signer), \
                 patch('creator.builder.run_tool', side_effect=tool), \
                 patch('creator.builder.shutil.copy2'), \
                 patch('creator.builder.sign_and_verify', side_effect=sign):
                if fail_on:
                    with self.assertRaises(BuildError):
                        build_installer(BuildSpec('https://example.com', 'Test App', None), output)
                    self.assertFalse((output / 'BUILD-INFO.json').exists())
                    return events, None
                installer = build_installer(BuildSpec('https://example.com', 'Test App', None), output)
                self.assertTrue(installer.is_file())
                metadata = json.loads((output / 'BUILD-INFO.json').read_text())
                return events, metadata

    def test_app_is_signed_before_packaging_and_installer_after(self):
        config = SigningConfig(Path('signtool.exe'), 'A' * 40, False, 'https://timestamp.example.com')
        events, metadata = self.exercise(config)
        self.assertEqual(events, ['compile', 'sign-app', 'package', 'sign-installer'])
        self.assertTrue(metadata['authenticode_verified'])

    def test_unsigned_build_is_labelled_unsigned(self):
        events, metadata = self.exercise(None)
        self.assertEqual(events, ['compile', 'package'])
        self.assertFalse(metadata['authenticode_verified'])

    def test_failed_app_signature_stops_packaging(self):
        config = SigningConfig(Path('signtool.exe'), 'A' * 40, False, 'https://timestamp.example.com')
        events, _ = self.exercise(config, 'sign-app')
        self.assertEqual(events, ['compile', 'sign-app'])

    def test_failed_installer_signature_does_not_report_success(self):
        config = SigningConfig(Path('signtool.exe'), 'A' * 40, False, 'https://timestamp.example.com')
        self.exercise(config, 'sign-installer')
