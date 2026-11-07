from io import BytesIO
import unittest

from PIL import Image
from creator.icons import default_icon, normalize_icon, ICON_SIZES, MAX_IMAGE_BYTES


class IconTests(unittest.TestCase):
    def test_transparency_aspect_ratio_and_all_windows_sizes(self):
        data = BytesIO()
        Image.new('RGBA', (400, 200), (51, 204, 153, 255)).save(data, format='PNG')
        result = normalize_icon(data.getvalue())
        with Image.open(BytesIO(result)) as icon:
            self.assertEqual(icon.format, 'ICO')
            self.assertEqual(icon.ico.sizes(), set(ICON_SIZES))
            image = icon.convert('RGBA')
            self.assertEqual(image.getpixel((128, 128)), (51, 204, 153, 255))
            self.assertEqual(image.getpixel((128, 0))[3], 0)

    def test_jpeg_and_ico_are_accepted(self):
        data = BytesIO()
        Image.new('RGB', (64, 64), 'red').save(data, format='JPEG')
        self.assertTrue(normalize_icon(data.getvalue()).startswith(b'\x00\x00\x01\x00'))
        self.assertTrue(normalize_icon(default_icon()).startswith(b'\x00\x00\x01\x00'))

    def test_invalid_and_oversized_data_rejected(self):
        for data in (b'not an image', b'<svg></svg>', b'', b'x' * (MAX_IMAGE_BYTES + 1)):
            with self.assertRaises(ValueError):
                normalize_icon(data)

    def test_extreme_dimensions_rejected_before_conversion(self):
        data = BytesIO()
        Image.new('L', (4001, 4001)).save(data, format='PNG')
        with self.assertRaisesRegex(ValueError, 'megapiksel'):
            normalize_icon(data.getvalue())
