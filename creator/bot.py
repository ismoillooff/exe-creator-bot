import asyncio
from contextlib import suppress
import logging
import json
import os
import time

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .builder import BuildError, BuildSpec, build_installer, doctor
from .config import ROOT
from .validation import normalize_url, password_record, validate_name
from .icons import MAX_IMAGE_BYTES, normalize_icon

CREATE = '🛠 EXE yaratish'
SKIP = '⏭ Parolsiz davom etish'
SKIP_ICON = '⏭ Standart ikonka'
CANCEL = '❌ Bekor qilish'
MENU = ReplyKeyboardMarkup([[CREATE]], resize_keyboard=True)
PASSWORD_MENU = ReplyKeyboardMarkup([[SKIP], [CANCEL]], resize_keyboard=True)
CANCEL_MENU = ReplyKeyboardMarkup([[CANCEL]], resize_keyboard=True)
ICON_MENU = ReplyKeyboardMarkup([[SKIP_ICON], [CANCEL]], resize_keyboard=True)
LOG = logging.getLogger('exe_creator')


class CreatorBot:
    def __init__(self, allowed_ids: set[int], cooldown: int = 60, max_pending: int = 5):
        self.allowed_ids = allowed_ids
        self.cooldown = cooldown
        self.max_pending = max_pending
        self.jobs: set[int] = set()
        self.last_build: dict[int, float] = {}
        self.semaphore = asyncio.Semaphore(1)

    async def permitted(self, update: Update) -> bool:
        if update.effective_chat is None or update.effective_user is None or update.message is None:
            return False
        if update.effective_chat.type != 'private':
            await update.message.reply_text("Botdan shaxsiy chatda foydalaning. Parolni guruhga yozmang.")
            return False
        if self.allowed_ids and update.effective_user.id not in self.allowed_ids:
            await update.message.reply_text("Sizga bu botdan foydalanishga ruxsat berilmagan.")
            return False
        return True

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.permitted(update):
            return
        context.user_data.clear()
        if update.effective_user.id in self.jobs:
            await update.message.reply_text("EXE tayyorlanmoqda. Natija shu chatga yuboriladi.", reply_markup=MENU)
            return
        await update.message.reply_text(
            "Salom! Sayt havolasidan Windows 10/11 x64 uchun o'rnatuvchi EXE yarataman.\n\n"
            "Bosqichlar: sayt havolasi → ikonka rasmi → dastur nomi → ixtiyoriy chiqish paroli.\n"
            "Dastur ramkasiz to'liq ekranda ochiladi, kichraytirish tugmalari bo'lmaydi.\n"
            "Boshlash uchun «EXE yaratish» tugmasini bosing.\n"
            "/cancel — kiritishni bekor qilish\n/id — Telegram ID ni ko'rish",
            reply_markup=MENU)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.permitted(update):
            return
        context.user_data.clear()
        text = ("EXE allaqachon yig'ilmoqda. Tugagach shu chatga yuboriladi."
                if update.effective_user.id in self.jobs else "Bekor qilindi.")
        await update.message.reply_text(text, reply_markup=MENU)

    async def identity(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.permitted(update):
            return
        await update.message.reply_text(f'Telegram ID: {update.effective_user.id}')

    async def text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.permitted(update):
            return
        message, user_id = update.message, update.effective_user.id
        value = message.text
        if value == CANCEL:
            await self.cancel(update, context)
            return
        if user_id in self.jobs:
            await message.reply_text("Oldingi EXE tayyorlanmoqda. Natijani kuting.")
            return
        if value == CREATE or value == '/create':
            context.user_data.clear()
            context.user_data.update(stage='url', updated=time.monotonic())
            await message.reply_text("Sayt havolasini kiriting. Masalan: https://example.com", reply_markup=CANCEL_MENU)
            return
        stage = context.user_data.get('stage')
        if stage and time.monotonic() - context.user_data.get('updated', 0) > 900:
            context.user_data.clear()
            await message.reply_text("15 daqiqa o'tdi. «EXE yaratish» orqali qayta boshlang.", reply_markup=MENU)
            return
        if not stage:
            await message.reply_text("Boshlash uchun «EXE yaratish» tugmasini bosing.", reply_markup=MENU)
            return
        try:
            if stage == 'url':
                context.user_data['url'] = normalize_url(value)
                context.user_data.update(stage='icon', updated=time.monotonic())
                await message.reply_text(
                    "Dastur ikonkasi uchun rasm yuboring (10 MB gacha).\n"
                    "Rasmni oddiy foto yoki PNG/JPG/WEBP/BMP/ICO fayl sifatida yuborishingiz mumkin.\n"
                    "Shu rasm EXE, dastur oynasi va ish stolidagi yorliqda ko'rinadi. "
                    "PNG fayl sifatida yuborsangiz shaffof fon saqlanadi.\n\n"
                    "Rasmsiz davom etish uchun «Standart ikonka» tugmasini bosing.", reply_markup=ICON_MENU)
            elif stage == 'icon':
                if value != SKIP_ICON:
                    await message.reply_text("Ikonka uchun rasm yuboring yoki «Standart ikonka» tugmasini bosing.", reply_markup=ICON_MENU)
                    return
                context.user_data['icon'] = None
                context.user_data.update(stage='name', updated=time.monotonic())
                await message.reply_text("EXE fayl nomini kiriting. Masalan: Mening Saytim", reply_markup=CANCEL_MENU)
            elif stage == 'name':
                context.user_data['name'] = validate_name(value)
                context.user_data.update(stage='password', updated=time.monotonic())
                await message.reply_text(
                    "Chiqish parolini kiriting (4–128 belgi) yoki «Parolsiz davom etish» tugmasini bosing.\n\n"
                    "Alt+F4 va «Chiqish» bosilganda shu parol so'raladi. Telegramga yozgan parolingizni "
                    "bot imkon qadar darhol o'chiradi. Boshqa hisoblarda ishlatadigan parolingizni kiritmang.",
                    reply_markup=PASSWORD_MENU)
            elif stage == 'password':
                if value == SKIP:
                    record = None
                else:
                    with suppress(TelegramError):
                        await message.delete()
                    record = await asyncio.to_thread(password_record, value)
                remaining = self.cooldown - (time.monotonic() - self.last_build.get(user_id, float('-inf')))
                if remaining > 0:
                    await message.reply_text(f"Yangi EXE uchun {int(remaining) + 1} soniya kuting, so'ng parolni qayta yuboring.")
                    return
                if len(self.jobs) >= self.max_pending:
                    await message.reply_text("Navbat to'lgan. Birozdan keyin parolni qayta yuboring yoki parolsiz davom eting.")
                    return
                spec = BuildSpec(context.user_data['url'], context.user_data['name'], record,
                                 context.user_data.get('icon'))
                context.user_data.clear()
                self.jobs.add(user_id)
                self.last_build[user_id] = time.monotonic()
                try:
                    await message.reply_text("⏳ EXE yaratish navbatiga qo'shildi. Tayyor bo'lganda yuboraman.", reply_markup=ReplyKeyboardRemove())
                except TelegramError:
                    self.jobs.discard(user_id)
                    raise
                context.application.create_task(self.deliver(spec, user_id, message.chat_id, context), update=update)
        except ValueError as error:
            await message.reply_text(str(error))

    async def image(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.permitted(update):
            return
        message = update.message
        if update.effective_user.id in self.jobs:
            await message.reply_text("Oldingi EXE tayyorlanmoqda. Natijani kuting.")
            return
        if context.user_data.get('stage') != 'icon':
            await message.reply_text("Rasm yuborishdan oldin «EXE yaratish» orqali sayt havolasini kiriting.")
            return
        if time.monotonic() - context.user_data.get('updated', 0) > 900:
            context.user_data.clear()
            await message.reply_text("15 daqiqa o'tdi. «EXE yaratish» orqali qayta boshlang.", reply_markup=MENU)
            return
        media = message.photo[-1] if message.photo else message.document
        if not media:
            await message.reply_text('Ikonka uchun PNG, JPG, WEBP, BMP yoki ICO rasm yuboring.')
            return
        if media.file_size is not None and media.file_size > MAX_IMAGE_BYTES:
            await message.reply_text('Rasm 10 MB dan kichik bo\'lishi kerak.')
            return
        try:
            remote = await media.get_file()
            if remote.file_size is not None and remote.file_size > MAX_IMAGE_BYTES:
                raise ValueError('Rasm 10 MB dan kichik bo\'lishi kerak.')
            data = await remote.download_as_bytearray(read_timeout=60)
            icon = await asyncio.to_thread(normalize_icon, bytes(data))
        except ValueError as error:
            await message.reply_text(str(error), reply_markup=ICON_MENU)
            return
        except TelegramError:
            await message.reply_text("Rasmni yuklab bo'lmadi. Qayta yuboring.", reply_markup=ICON_MENU)
            return
        context.user_data.update(icon=icon, stage='name', updated=time.monotonic())
        await message.reply_text("✅ Ikonka qabul qilindi. Endi EXE fayl nomini kiriting.", reply_markup=CANCEL_MENU)

    async def deliver(self, spec: BuildSpec, user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            async with self.semaphore:
                await context.bot.send_message(chat_id, "⚙️ Windows o'rnatuvchisi yig'ilmoqda…")
                installer = await asyncio.to_thread(build_installer, spec)
            metadata = json.loads((installer.parent / 'BUILD-INFO.json').read_text(encoding='utf-8'))
            signature_note = ("Raqamli imzo tekshirildi." if metadata['authenticode_verified']
                              else "EXE imzosiz: Windows Application Control uni bloklashi mumkin.")
            with installer.open('rb') as file:
                await context.bot.send_document(
                    chat_id, document=file, filename=installer.name,
                    caption=(f"✅ {spec.name} tayyor!\nWindows 10/11 x64. EXE ni ochib o'rnating.\n"
                             + ("Chiqish parol bilan himoyalangan." if spec.password else "Chiqish parolsiz.")
                             + "\nRamkasiz to'liq ekran rejimi."
                             + "\n" + signature_note
                             + "\nWebView2 yo'q bo'lsa o'rnatish vaqtida internet kerak."),
                    reply_markup=MENU, write_timeout=180, read_timeout=180)
            LOG.info('Build delivered: user=%s file=%s', user_id, installer.name)
        except BuildError:
            LOG.exception('Build failed: user=%s', user_id)
            with suppress(TelegramError):
                await context.bot.send_message(chat_id, "EXE yaratishda xatolik. Serverdagi kompilyator va .tools fayllarini tekshiring, so'ng qayta urinib ko'ring.", reply_markup=MENU)
        except TelegramError as error:
            # Telegram xatosi matni tokenli URL saqlashi mumkin: faqat turini yozamiz.
            LOG.error('Telegram delivery failed: user=%s type=%s', user_id, type(error).__name__)
            with suppress(TelegramError):
                await context.bot.send_message(chat_id, "Yuborish amalga oshmadi. Yaratilgan fayl serverning dist papkasida saqlandi.", reply_markup=MENU)
        except Exception as error:
            LOG.error('Unexpected build failure: user=%s type=%s', user_id, type(error).__name__)
            with suppress(TelegramError):
                await context.bot.send_message(chat_id, "Ichki xatolik. Server konsolini tekshiring.", reply_markup=MENU)
        finally:
            self.jobs.discard(user_id)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    LOG.error('Update processing failed: %s', type(context.error).__name__)


def main() -> None:
    load_dotenv(ROOT / '.env')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    token = os.getenv('BOT_TOKEN', '').strip()
    if not token or ':' not in token:
        raise SystemExit(".env fayliga @BotFather bergan BOT_TOKEN ni kiriting. .env.example dan nusxa oling.")
    errors = doctor()
    if errors:
        raise SystemExit('\n'.join(errors))
    try:
        allowed = {int(value.strip()) for value in os.getenv('ALLOWED_USER_IDS', '').split(',') if value.strip()}
        cooldown = max(0, int(os.getenv('BUILD_COOLDOWN_SECONDS', '60')))
        max_pending = max(1, int(os.getenv('MAX_PENDING_BUILDS', '5')))
    except ValueError:
        raise SystemExit('.env ichida ID, kutish va navbat qiymatlari son bo\'lishi kerak.') from None
    bot = CreatorBot(allowed, cooldown, max_pending)
    application = Application.builder().token(token).concurrent_updates(False).build()
    application.add_handler(CommandHandler(['start', 'help'], bot.start))
    application.add_handler(CommandHandler('cancel', bot.cancel))
    application.add_handler(CommandHandler('id', bot.identity))
    application.add_handler(CommandHandler('create', bot.text))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, bot.image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.text))
    application.add_error_handler(on_error)
    LOG.info('Bot starting. Stop: Ctrl+C. Building: Windows x64 / WebView2.')
    try:
        application.run_polling(allowed_updates=['message'], drop_pending_updates=True)
    except TelegramError as error:
        raise SystemExit(f'Telegramga ulanish xatosi: {type(error).__name__}. Token va internetni tekshiring.') from None


if __name__ == '__main__':
    main()
