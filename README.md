# Telegram Disappearing Media Saver

by mrdv71

Save incoming self-destructing **photos, videos, and audio/voice messages from Telegram** onto your own computer or server. Uses Telethon and your own Telegram account, not a bot. Only media Telegram exposes with a TTL marker in regular private cloud chats is eligible; support depends on Telegram's API and the media still being available.

## Run locally or on a server

Choose your own **Mac/Linux/Windows computer** or an **always-on Linux server**.
See [deployment options](DEPLOYMENT.md) for persistent storage, interactive login,
and an optional systemd service with boot startup and automatic restart.
The local commands below still work without installing a service.

## Setup (macOS / Linux)

Install Python 3.10+ and Git, then:

```sh
git clone https://github.com/mrdv71/telegram-disappearing-media-saver.git
cd telegram-disappearing-media-saver
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python saver.py --login
python saver.py
```

Get your own API ID and API hash at https://my.telegram.org/apps. The login command prompts locally for those values, your phone number, Telegram login code, and optional two-step verification password. Do not paste credentials into GitHub or a chat.

Default destination: `~/Downloads/TelegramDisappearingMedia`.

```sh
# Choose your destination
python saver.py --output "$HOME/Downloads/MyTelegramMedia"
# See options
python saver.py --help
```

## Windows (PowerShell)

```powershell
git clone https://github.com/mrdv71/telegram-disappearing-media-saver.git
cd telegram-disappearing-media-saver
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe saver.py --login
.\.venv\Scripts\python.exe saver.py
```

Windows instructions are provided but have not been tested on Windows. Restrict access to the state folder using your operating system's account/file permissions.

## Behavior and limits

- Watches incoming disappearing media in all private cloud chats; skips outgoing messages, groups, and ordinary non-TTL media.
- Handles photos and documents (Telegram uses documents for video/audio/voice).
- On first run, checks the previous 24 hours; later runs recover from the last successful checkpoint with a short overlap. Runs another check every minute.
- Deduplicates successful downloads using account/chat/message identifiers stored only on your computer.
- Secret Chats are not supported. This cannot recover media already expired, deleted, or no longer downloadable. View-once behavior is not guaranteed.
- The computer must stay awake, online, and running the command. Ctrl-C stops the program; closing Terminal stops it. The basic command installs no service; optional server service instructions are in DEPLOYMENT.md.
- Use only with media you have permission to retain. Disappearing messages do not imply permission to keep them.

## Private local state

Your login session, API credentials, and recovery checkpoint are stored outside the repository in `~/.telegram-disappearing-media-saver/`. On macOS/Linux, the program uses owner-only permissions for newly created state and output files. Phone/code/2FA values are prompted, not included in the repository. The session grants account access: do not share it. Revoke it through Telegram Settings → Devices when no longer needed.

The repository contains source and instructions only: no account sessions, downloaded media, contacts, message history, notification bot settings, or original private Git history. Filenames and local logs can contain sender/message identifiers; those stay on your computer.

## Verification

Offline checks cover syntax, command help, eligibility filters, and deduplication. No real Telegram account or private media is used in release tests; actual live Telegram downloads and Windows behavior are unverified in this source-only edition.

Based on our local media-saver workflow, with private edit/delete notification integration removed. Telethon is an external dependency with its own license.
