import base64
import hashlib
import unittest

from creator.validation import normalize_url, password_record, validate_name


class ValidationTests(unittest.TestCase):
    def test_url_accepts_web_and_normalizes(self):
        self.assertEqual(normalize_url('example.com'), 'https://example.com/')
        self.assertEqual(normalize_url('http://localhost:8080/app?q=salom#part'),
                         'http://localhost:8080/app?q=salom#part')
        self.assertEqual(normalize_url('https://[::1]:443/'), 'https://[::1]:443/')
        self.assertIn('xn--', normalize_url('https://münich.de/'))

    def test_url_rejects_local_files_commands_credentials_and_bad_ports(self):
        for value in ('', 'file:///C:/secret', 'javascript:alert(1)', 'ftp://example.com',
                      'https://a:b@example.com/', 'https://example.com:99999',
                      'https://a\\b.com/', 'https://a.com/\nsecret', 'https://-bad.com', 'https://a..com'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_url(value)

    def test_windows_filename(self):
        self.assertEqual(validate_name(' Mening Saytim.exe '), 'Mening Saytim')
        self.assertEqual(validate_name("O'quv Markazi"), "O'quv Markazi")
        for value in ('CON', 'nul.txt', 'COM1', 'LPT¹', '../evil', 'C:\\app', 'x{app}', 'a"b', 'a.', 'a' * 61):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_name(value)

    def test_password_digest_and_optional_password(self):
        self.assertIsNone(password_record(None))
        secret = '  Salom🔒123  '
        record = password_record(secret)
        result = hashlib.pbkdf2_hmac('sha256', secret.encode(), base64.b64decode(record['Salt']), record['Iterations'])
        self.assertEqual(result, base64.b64decode(record['Hash']))
        self.assertNotEqual(password_record(secret)['Salt'], record['Salt'])
        self.assertNotIn(secret, str(record))
        for value in ('', '123', 'x' * 129):
            with self.assertRaises(ValueError):
                password_record(value)


if __name__ == '__main__':
    unittest.main()
