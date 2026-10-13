"""Private-chat disappearing media saver with local persistent authorization."""
import asyncio
import getpass
import os
import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from telethon import TelegramClient, events, functions



def report(*parts):
    print(datetime.now().astimezone().isoformat(timespec='seconds'), *parts, flush=True)


async def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description='Save incoming disappearing Telegram cloud-chat media locally.')
    parser.add_argument('--login', action='store_true', help='Interactively authorize your own Telegram account')
    parser.add_argument('--output', type=Path, default=Path.home() / 'Downloads' / 'TelegramDisappearingMedia')
    parser.add_argument('--state-dir', type=Path, default=Path.home() / '.telegram-disappearing-media-saver')
    args = parser.parse_args()
    state = args.state_dir.expanduser().resolve()
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    state.chmod(0o700)
    cfgpath = state / 'config.json'
    if cfgpath.exists():
        config = json.loads(cfgpath.read_text())
    elif args.login:
        config = {'api_id': int(input('API ID from my.telegram.org/apps: ').strip()),
                  'api_hash': getpass.getpass('API hash (hidden): ').strip()}
    else:
        parser.error('Run with --login first.')
    api_id, api_hash = config['api_id'], config['api_hash']
    session = str(state / 'account')
    client = TelegramClient(session, api_id, api_hash,
                            device_model='Telegram Media Saver',
                            request_retries=2, flood_sleep_threshold=30)
    try:
        if args.login:
            await client.start(
                phone=lambda: getpass.getpass('Phone with country code (hidden): ').strip(),
                code_callback=lambda: getpass.getpass('Telegram login code (hidden): '),
                password=lambda: getpass.getpass('Telegram 2FA password (hidden): '))
            cfgpath.write_text(json.dumps(config))
            cfgpath.chmod(0o600)
            report('Login saved locally. Run without --login to receive media.')
            return
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError('Login required: run with --login.')
        me = await client.get_me()
        folder = args.output.expanduser().resolve()
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        import tempfile
        with tempfile.TemporaryFile(dir=folder) as check:
            check.write(b'write check')
        report('Telegram login verified; output folder is writable.')
        queue = asyncio.Queue(maxsize=100)
        checkpoint = state / 'recovery.json'
        recovery = json.loads(checkpoint.read_text()) if checkpoint.exists() else {
            'since': (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat(),
            'saved': [],
        }
        saved_ids = set(recovery['saved'])
        pending = set()
        failures = 0

        def persist():
            recovery['saved'] = sorted(saved_ids)
            temporary = checkpoint.with_suffix('.tmp')
            temporary.write_text(json.dumps(recovery))
            temporary.replace(checkpoint)

        async def enqueue(msg):
            key = f"{me.id}:{msg.chat_id}:{msg.id}"
            if (not msg.is_private or msg.out or not msg.sender_id
                    or msg.sender_id == me.id or msg.chat_id != msg.sender_id
                    or not getattr(msg.media, 'ttl_seconds', None)
                    or not (getattr(msg.media, 'photo', None) or
                            getattr(msg.media, 'document', None))
                    or key in saved_ids or key in pending):
                return
            pending.add(key)
            await queue.put(msg)

        persist()

        async def on_message(event):
            if (not event.is_private or event.out
                    or not event.sender_id or event.sender_id == me.id
                    or event.chat_id != event.sender_id or not event.message.media):
                return
            if not getattr(event.message.media, 'ttl_seconds', None):
                return
            await enqueue(event.message)

        async def save_messages():
            nonlocal failures
            import tempfile
            from datetime import datetime
            while True:
                msg = await queue.get()
                key = f"{me.id}:{msg.chat_id}:{msg.id}"
                stamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                run_dir = None
                try:
                    run_dir = Path(tempfile.mkdtemp(
                        prefix=f'{stamp}_sender-{msg.sender_id}_{msg.id}_', dir=str(folder)))
                    saved = await asyncio.wait_for(
                        client.download_media(msg, file=str(run_dir / 'media')), 120)
                    if saved and Path(saved).is_file() and Path(saved).stat().st_size:
                        saved_ids.add(key)
                        persist()
                        print('Saved:', saved, flush=True)
                    else:
                        failures += 1
                        print('No media returned for message', msg.id, flush=True)
                except Exception as exc:
                    failures += 1
                    report('Download failed:', type(exc).__name__, '| message:', msg.id)
                    if run_dir is not None:
                        try:
                            for partial in run_dir.iterdir():
                                if partial.is_file():
                                    partial.rename(partial.with_name(partial.name + '.partial'))
                        except OSError as cleanup_error:
                            report('Partial-file cleanup failed:', type(cleanup_error).__name__)
                finally:
                    pending.discard(key)
                    queue.task_done()

        client.add_event_handler(on_message, events.NewMessage(incoming=True))
        worker = asyncio.create_task(save_messages())
        async def check_connection():
            while True:
                await asyncio.wait_for(client(functions.updates.GetStateRequest()), 30)
                report('Connection health: OK')
                await asyncio.sleep(60)

        health = asyncio.create_task(check_connection())
        async def recover_missed():
            while True:
                started = datetime.now(timezone.utc)
                cutoff = datetime.fromisoformat(recovery['since']) - timedelta(seconds=60)
                before = failures
                report('Checking missed arrivals since', cutoff.isoformat())
                async for dialog in client.iter_dialogs():
                    if not dialog.is_user or not dialog.date or dialog.date < cutoff:
                        continue
                    async for msg in client.iter_messages(dialog.entity):
                        if msg.date < cutoff:
                            break
                        await enqueue(msg)
                await queue.join()
                if failures == before:
                    recovery['since'] = started.isoformat()
                    persist()
                report('Missed-arrival check complete; failed downloads:', failures - before)
                await asyncio.sleep(60)

        recovery_task = asyncio.create_task(recover_missed())
        receiver = asyncio.create_task(client.run_until_disconnected())
        print('Ready: saving new disappearing media from ALL private chats (no usernames needed).', flush=True)
        print('Save folder:', folder, flush=True)
        print('Press Control-C to stop. Keep this computer awake and online.', flush=True)
        print('Cloud private chats only; Secret Chats and expired media are not supported.', flush=True)
        try:
            done, _ = await asyncio.wait(
                [receiver, health, worker, recovery_task],
                return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                task.result()
        finally:
            client.remove_event_handler(on_message)
            tasks = [worker, health, receiver, recovery_task]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        await client.disconnect()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nStopped. Login remains local; revoke it in Telegram Settings > Devices if desired.')
    except Exception as exc:
        # Avoid exposing account data or credential-bearing exception bodies.
        print(f'Stopped ({type(exc).__name__}). Check login, network, and folder permissions; private details suppressed.')
        raise SystemExit(1)
