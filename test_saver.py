"""Offline tests of the actual enqueue function; no Telegram connection."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import subprocess
import sys
import tempfile


class FilterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        tree = ast.parse(Path(__file__).with_name('saver.py').read_text())
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == 'enqueue')
        self.env = dict(me=NS(id=1), saved_ids=set(), pending=set(), queue=asyncio.Queue())
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<enqueue>', 'exec'), self.env)

    def msg(self, **changes):
        fields = dict(id=10, is_private=True, out=False, sender_id=2, chat_id=2,
                      media=NS(ttl_seconds=5, photo=True, document=None))
        fields.update(changes)
        return NS(**fields)

    async def test_photo_and_documents(self):
        await self.env['enqueue'](self.msg())
        await self.env['enqueue'](self.msg(id=11, media=NS(ttl_seconds=5, photo=None, document=True)))
        self.assertEqual(self.env['queue'].qsize(), 2)

    async def test_excluded_messages(self):
        for changes in (dict(out=True), dict(is_private=False), dict(sender_id=1, chat_id=1),
                        dict(media=None), dict(media=NS(ttl_seconds=None, photo=True)),
                        dict(chat_id=-1), dict(media=NS(ttl_seconds=5, photo=None, document=None))):
            await self.env['enqueue'](self.msg(**changes))
        self.assertEqual(self.env['queue'].qsize(), 0)

    async def test_pending_and_saved_duplicates(self):
        await self.env['enqueue'](self.msg())
        await self.env['enqueue'](self.msg())
        self.env['saved_ids'].add('1:2:11')
        await self.env['enqueue'](self.msg(id=11))
        self.assertEqual(self.env['queue'].qsize(), 1)

    async def test_same_message_id_different_chats(self):
        await self.env['enqueue'](self.msg())
        await self.env['enqueue'](self.msg(sender_id=3, chat_id=3))
        self.assertEqual(self.env['queue'].qsize(), 2)


class ErrorPrivacyTests(unittest.TestCase):
    def test_invalid_local_config_does_not_print_private_details(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'config.json').write_text('synthetic-private-marker-invalid-json')
            result = subprocess.run(
                [sys.executable, str(Path(__file__).with_name('saver.py')),
                 '--state-dir', tmp], capture_output=True, text=True)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 1)
            self.assertIn('JSONDecodeError', output)
            self.assertNotIn('synthetic-private-marker', output)
            self.assertNotIn(tmp, output)
            self.assertNotIn('Traceback', output)


if __name__ == '__main__':
    unittest.main()
