import asyncio
from io import BytesIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from PIL import Image
from creator.bot import CANCEL, CREATE, SKIP, SKIP_ICON, CreatorBot
from creator.builder import BuildError
from creator.config import ROOT


def update(text, user=123, chat_type='private'):
    message = SimpleNamespace(text=text, chat_id=user, reply_text=AsyncMock(), delete=AsyncMock(), photo=[], document=None)
    return SimpleNamespace(message=message, effective_user=SimpleNamespace(id=user),
                           effective_chat=SimpleNamespace(type=chat_type))


class BotTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = CreatorBot(set(), cooldown=0)
        self.context = SimpleNamespace(user_data={}, application=SimpleNamespace(create_task=Mock()),
                                       bot=SimpleNamespace(send_message=AsyncMock(), send_document=AsyncMock()))

    async def flow_to_password(self):
        for text in (CREATE, 'example.com', SKIP_ICON, 'Test App'):
            await self.bot.text(update(text), self.context)
        self.assertEqual(self.context.user_data['stage'], 'password')

    def close_queued_coroutine(self):
        coro = self.context.application.create_task.call_args.args[0]
        coro.close()  # Test tashqi Telegram yoki real kompilyatorga ulanmaydi.

    async def test_skip_queues_build_with_no_password(self):
        await self.flow_to_password()
        await self.bot.text(update(SKIP), self.context)
        self.assertIn(123, self.bot.jobs)
        self.assertEqual(self.context.user_data, {})
        coro = self.context.application.create_task.call_args.args[0]
        self.assertIsNone(coro.cr_frame.f_locals['spec'].password)
        self.close_queued_coroutine()

    async def test_password_message_deleted_and_only_hash_queued(self):
        await self.flow_to_password()
        event = update('parol123')
        await self.bot.text(event, self.context)
        event.message.delete.assert_awaited_once()
        coro = self.context.application.create_task.call_args.args[0]
        record = coro.cr_frame.f_locals['spec'].password
        self.assertEqual(record['Iterations'], 210000)
        self.assertNotIn('parol123', str(record))
        self.close_queued_coroutine()

    async def test_invalid_values_keep_current_stage(self):
        await self.bot.text(update(CREATE), self.context)
        await self.bot.text(update('file:///C:/test'), self.context)
        self.assertEqual(self.context.user_data['stage'], 'url')
        await self.bot.text(update('example.com'), self.context)
        self.assertEqual(self.context.user_data['stage'], 'icon')
        await self.bot.text(update(SKIP_ICON), self.context)
        await self.bot.text(update('CON'), self.context)
        self.assertEqual(self.context.user_data['stage'], 'name')

    async def test_cancel_resets_flow_and_group_is_rejected(self):
        await self.flow_to_password()
        await self.bot.text(update(CANCEL), self.context)
        self.assertEqual(self.context.user_data, {})
        await self.bot.text(update(CREATE, chat_type='group'), self.context)
        self.assertEqual(self.context.user_data, {})

    async def test_allowlist(self):
        restricted = CreatorBot({999})
        await restricted.text(update(CREATE), self.context)
        self.assertEqual(self.context.user_data, {})

    async def test_failure_releases_user_slot(self):
        from creator.builder import BuildSpec
        self.bot.jobs.add(123)
        with patch('creator.bot.build_installer', side_effect=BuildError('Test compiler failure')):
            with self.assertLogs('exe_creator', level='ERROR'):
                await self.bot.deliver(BuildSpec('https://example.com', 'Test', None), 123, 123, self.context)
        self.assertNotIn(123, self.bot.jobs)

    async def test_busy_user_cannot_create_duplicate_job(self):
        self.bot.jobs.add(123)
        await self.bot.text(update(CREATE), self.context)
        self.context.application.create_task.assert_not_called()
        self.assertEqual(self.context.user_data, {})

    async def test_delivery_reports_actual_signature_metadata(self):
        from creator.builder import BuildSpec
        (ROOT / 'work').mkdir(exist_ok=True)
        for signed in (False, True):
            with self.subTest(signed=signed), tempfile.TemporaryDirectory(dir=ROOT / 'work') as directory:
                installer = Path(directory) / 'Test-Setup.exe'
                installer.write_bytes(b'MZ-test')
                (installer.parent / 'BUILD-INFO.json').write_text(json.dumps({'authenticode_verified': signed}))
                self.bot.jobs.add(123)
                with patch('creator.bot.build_installer', return_value=installer):
                    await self.bot.deliver(BuildSpec('https://example.com', 'Test', None), 123, 123, self.context)
                caption = self.context.bot.send_document.call_args.kwargs['caption']
                self.assertIn('Raqamli imzo tekshirildi.' if signed else 'EXE imzosiz:', caption)
                self.assertNotIn(123, self.bot.jobs)

    async def test_photo_step_and_custom_icon_reaches_build(self):
        await self.bot.text(update(CREATE), self.context)
        await self.bot.text(update('example.com'), self.context)
        self.assertEqual(self.context.user_data['stage'], 'icon')
        data = BytesIO()
        Image.new('RGBA', (300, 180), '#33cc99').save(data, format='PNG')
        remote = SimpleNamespace(file_size=len(data.getvalue()), download_as_bytearray=AsyncMock(return_value=bytearray(data.getvalue())))
        media = SimpleNamespace(file_size=len(data.getvalue()), get_file=AsyncMock(return_value=remote))
        event = update(None)
        event.message.photo = [media]
        await self.bot.image(event, self.context)
        self.assertEqual(self.context.user_data['stage'], 'name')
        self.assertEqual(self.context.user_data['icon'][:4], b'\x00\x00\x01\x00')
        await self.bot.text(update('Custom Icon'), self.context)
        await self.bot.text(update(SKIP), self.context)
        coro = self.context.application.create_task.call_args.args[0]
        self.assertIsNotNone(coro.cr_frame.f_locals['spec'].icon)
        self.close_queued_coroutine()

    async def test_invalid_image_keeps_icon_step(self):
        await self.bot.text(update(CREATE), self.context)
        await self.bot.text(update('example.com'), self.context)
        remote = SimpleNamespace(file_size=10, download_as_bytearray=AsyncMock(return_value=bytearray(b'not image')))
        event = update(None)
        event.message.document = SimpleNamespace(file_size=10, get_file=AsyncMock(return_value=remote))
        await self.bot.image(event, self.context)
        self.assertEqual(self.context.user_data['stage'], 'icon')

    async def test_oversized_image_is_not_downloaded(self):
        await self.bot.text(update(CREATE), self.context)
        await self.bot.text(update('example.com'), self.context)
        event = update(None)
        event.message.document = SimpleNamespace(file_size=11 * 1024 * 1024, get_file=AsyncMock())
        await self.bot.image(event, self.context)
        event.message.document.get_file.assert_not_awaited()
        self.assertEqual(self.context.user_data['stage'], 'icon')
