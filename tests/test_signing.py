import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from creator.signing import SigningConfig, SigningError, sign_and_verify, signing_config


class SigningTests(unittest.TestCase):
    def test_unsigned_is_default_and_required_is_enforced(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(signing_config())
        with patch.dict(os.environ, {'REQUIRE_SIGNED_BUILDS': '1'}, clear=True):
            with self.assertRaises(SigningError):
                signing_config()

    def test_invalid_settings_are_rejected(self):
        cases = [
            {'REQUIRE_SIGNED_BUILDS': 'maybe'},
            {'SIGN_CERT_SHA1': 'not-a-thumbprint'},
            {'SIGN_CERT_SHA1': 'A' * 40, 'SIGN_CERT_STORE': 'RandomStore'},
            {'SIGN_CERT_SHA1': 'A' * 40, 'SIGN_TIMESTAMP_URL': 'file:///test'},
            {'SIGN_CERT_SHA1': 'A' * 40, 'SIGN_TIMESTAMP_URL': 'https://user:pass@example.com'},
        ]
        for env in cases:
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True), self.assertRaises(SigningError):
                signing_config()

    def test_configuration_normalizes_thumbprint_and_finds_tool(self):
        env = {'SIGN_CERT_SHA1': 'aa ' * 20, 'SIGN_CERT_STORE': 'LocalMachine'}
        with patch.dict(os.environ, env, clear=True), patch('creator.signing.find_signtool', return_value=Path('signtool.exe')):
            config = signing_config()
        self.assertEqual(config.thumbprint, 'AA' * 20)
        self.assertTrue(config.machine_store)

    def test_signing_uses_store_and_verifies_authenticode(self):
        config = SigningConfig(Path('signtool.exe'), 'A' * 40, True, 'https://timestamp.example.com')
        with patch('creator.signing.subprocess.run', return_value=subprocess.CompletedProcess([], 0, b'', b'')) as run:
            sign_and_verify(Path('app.exe'), config)
        self.assertEqual(run.call_count, 2)
        sign = run.call_args_list[0].args[0]
        verify = run.call_args_list[1].args[0]
        self.assertIn('/sm', sign)
        self.assertIn('/sha1', sign)
        self.assertIn('/tr', sign)
        self.assertIn('SHA256', sign)
        self.assertEqual(verify[1:5], ['verify', '/pa', '/all', '/tw'])
        self.assertNotIn('shell', run.call_args.kwargs)

    def test_sign_failure_and_missing_timestamp_do_not_pass(self):
        config = SigningConfig(Path('signtool.exe'), 'A' * 40, False, 'https://timestamp.example.com')
        for code in (1, 2):  # SignTool 2: warnings, jumladan timestamp muammolari.
            with self.subTest(code=code), patch('creator.signing.subprocess.run', return_value=subprocess.CompletedProcess([], code, b'', b'Failed')):
                with self.assertRaises(SigningError):
                    sign_and_verify(Path('app.exe'), config)

    def test_timeout_is_reported_as_signing_error(self):
        config = SigningConfig(Path('signtool.exe'), 'A' * 40, False, 'https://timestamp.example.com')
        with patch('creator.signing.subprocess.run', side_effect=subprocess.TimeoutExpired('signtool', 180)):
            with self.assertRaises(SigningError):
                sign_and_verify(Path('app.exe'), config)
