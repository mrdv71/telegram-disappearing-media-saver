# Telegram Disappearing Media Saver

by mrdv71

Save available incoming disappearing photos, videos, and audio from Telegram private cloud chats to your own computer or server. Uses your personal Telegram account, not a bot.

## Choose one setup

- **Your Mac, Linux computer, or Windows PC:** follow the steps below. Keep it awake and the terminal open.
- **An always-on Linux server:** follow the [server guide](DEPLOYMENT.md). It includes automatic startup and restart.

GitHub stores the code; it does not run the program. Each user provides their own Telegram account and credentials. Installing this repository does not migrate or change another installation.

## 1. Get your Telegram credentials

1. Sign in at [my.telegram.org/apps](https://my.telegram.org/apps) and create an application to get your **API ID** and **API hash**.
2. Have your phone number (including country code), Telegram login code, and two-step verification password (if enabled) ready.

Enter these values only when the local setup command asks. Hidden inputs show no characters while you type; this is normal. Never put credentials in GitHub issues or commits.

## 2. Install Python and Git

Use **Python 3.10 or newer** (3.12 recommended) and Git.

- **Mac:** install Python from [python.org](https://www.python.org/downloads/macos/). Run `git --version`; if macOS offers Command Line Tools, install them before continuing.
- **Ubuntu 24.04 / Debian 12 or newer:** run `sudo apt update`, then `sudo apt install -y python3 python3-venv git`.
- **Windows:** install Python from [python.org](https://www.python.org/downloads/windows/) with the Python launcher, and Git from [git-scm.com](https://git-scm.com/downloads/win). Reopen PowerShell afterward.

Check `python3 --version` and `git --version` on Mac/Linux, or `py -3 --version` and `git --version` on Windows. Stop and fix missing tools or a Python version below 3.10 before continuing.

## 3. Download and install

Run the commands **one line at a time**. Continue only if the previous command succeeds. Choose the block for your operating system. These commands are for a new installation; if you already cloned this repository, enter that folder instead of cloning it again.

### Mac / Linux — Terminal

```sh
git clone https://github.com/mrdv71/telegram-disappearing-media-saver.git
cd telegram-disappearing-media-saver
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### Windows — PowerShell

```powershell
git clone https://github.com/mrdv71/telegram-disappearing-media-saver.git
cd telegram-disappearing-media-saver
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

No virtual-environment activation is needed. Keep using the Python path shown below.

## 4. Sign in once

**Mac / Linux:**

```sh
.venv/bin/python saver.py --login
```

**Windows:**

```powershell
.\.venv\Scripts\python.exe saver.py --login
```

Follow the prompts. Success prints `Login saved locally`. Do not repeat setup on every start.

## 5. Start and check

**Mac / Linux:**

```sh
.venv/bin/python saver.py
```

**Windows:**

```powershell
.\.venv\Scripts\python.exe saver.py
```

Wait for `Ready: saving new disappearing media`. From a second account, send supported disappearing media to the signed-in account in a regular private cloud chat. Look for `Saved:` and open the file in `Downloads/TelegramDisappearingMedia` under your home folder. Ordinary photos without a disappearing/TTL marker are intentionally ignored. Telegram may not expose view-once media for download.

Press **Ctrl+C** to stop. To start again, open a terminal in this repository folder and repeat **step 5 only**. Closing the terminal, sleeping, or shutting down the computer interrupts collection. On Mac, you can use `caffeinate -i .venv/bin/python saver.py` to prevent idle sleep while running; this does not guarantee operation with the lid closed.

## If something fails

- **File not found / cannot open script:** enter the cloned repository folder first.
- **Missing module:** repeat the install command in step 3 using the same `.venv` Python.
- **Login/setup missing:** complete step 4, then start again with the same data directory.
- **Database locked:** stop other copies using the same session; run only one process per data directory.
- **No saved media or alerts:** repeat the exact test in step 5, check the network, and read the limits below.

Windows instructions are provided but Windows operation has not been verified. On Windows, restrict the private data folder to your own user account using folder permissions.

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
