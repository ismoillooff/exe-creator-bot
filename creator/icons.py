"""Telegram rasmini Windows uchun ko'p o'lchamli ICO ga aylantirish."""
from functools import lru_cache
from io import BytesIO
import warnings

from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
ICON_SIZES = [(size, size) for size in (16, 24, 32, 48, 64, 128, 256)]


def normalize_icon(data: bytes) -> bytes:
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError('Ikonka rasmi 10 MB dan kichik bo\'lishi kerak.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format not in ('PNG', 'JPEG', 'WEBP', 'ICO', 'BMP'):
                    raise ValueError('PNG, JPG, WEBP, BMP yoki ICO formatdagi rasm yuboring.')
                if source.width * source.height > MAX_IMAGE_PIXELS:
                    raise ValueError('Rasm o\'lchami juda katta: 16 megapikselgacha rasm yuboring.')
                image = ImageOps.exif_transpose(source).convert('RGBA')
                fitted = ImageOps.contain(image, (256, 256), Image.Resampling.LANCZOS)
                canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
                canvas.alpha_composite(fitted, ((256 - fitted.width) // 2, (256 - fitted.height) // 2))
                output = BytesIO()
                # .NET Framework Icon.ToBitmap uchun DIB freymlar; PNG-only ICO mos kelmaydi.
                canvas.save(output, format='ICO', sizes=ICON_SIZES, bitmap_format='bmp')
                return output.getvalue()
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombWarning,
            Image.DecompressionBombError) as error:
        raise ValueError('Rasmni o\'qib bo\'lmadi. Boshqa PNG yoki JPG rasm yuboring.') from error


@lru_cache(maxsize=1)
def default_icon() -> bytes:
    image = Image.new('RGBA', (256, 256))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 248, 248), radius=52, fill='#2563eb')
    draw.ellipse((48, 48, 208, 208), outline='white', width=9)
    draw.ellipse((91, 48, 165, 208), outline='white', width=8)
    draw.line((50, 128, 206, 128), fill='white', width=8)
    draw.arc((50, 77, 206, 179), 0, 180, fill='white', width=7)
    draw.arc((50, 77, 206, 179), 180, 360, fill='white', width=7)
    output = BytesIO()
    image.save(output, format='ICO', sizes=ICON_SIZES, bitmap_format='bmp')
    return output.getvalue()
