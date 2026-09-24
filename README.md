# Discord Popup Bot

This program connects to Discord and displays fullscreen images or GIFs, with
sound, on the computer running the bot. It is intended for Linux desktops with
a graphical session and also for microslop (windows).

## Requirements

- Python 3.13
- A Discord bot account and its token
- A Linux graphical session with working audio / working pc

The bot only responds to the Discord user IDs configured in `pipe.py`. Update
the `allowed` and `admin` lists before running it if different users should be
able to use the bot.

## Discord bot setup

1. Open the [Discord Developer Portal](https://discord.com/developers/applications)
	 and create an application.
2. Open **Bot**, create the bot, and copy its token. Keep the token private.
3. Enable **Message Content Intent** under the bot's privileged gateway intents.
4. Invite the bot to your server with permission to view channels and send
	 messages.

## Installation

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install discord.py PyQt5 sounddevice soundfile
```

`sounddevice` requires the PortAudio library in your operating system.:

```bash
sudo apt install libportaudio2
```
Arch linux:
```bash
sudo pacman -S portaudio
```
Edit the `MEDIA_PATH` value near the top of
`pipe.py` to the absolute path containing the media files (all media png gif and audio need to be in one folder!!!).

## Asset format

Each command uses the filename without its extension. A static image needs a
matching `.png` and `.wav`; an animation needs a matching `.gif` and `.wav`. (can be only `.png` and `.gif` audio can be in `.wav` `.mp3` `.ogg` `.flac` and others (manual setup!!!))
For example:

```text
image_popup/
├── pipe.png
├── pipe.wav
├── pipe.mp3
├── chad.gif
└── chad.wav
```

## Running

Set the bot token in the environment and start the program:

```bash
export DISCORD_TOKEN='paste-your-bot-token-here'
python pipe.py
```

The terminal should print a message similar to `Bot connected as ...` after the
bot logs in. Leave this process running while using the bot. Press `Ctrl+C` to
stop it.

For a one-time run without exporting the variable first:

```bash
DISCORD_TOKEN='paste-your-bot-token-here' python pipe.py
```

## Discord commands

Send the asset name in a channel the bot can read. Add a number to repeat the
popup; repeats are capped at 100 by default.

```text
pipe       # show pipe.png and play pipe.wav once
pipe 3     # show it three times
chad       # show chad.gif and play chad.wav once
```

`cinema` uses `cinema.png` and `cinema.wav`. The `check` command is available
only to users in the configured `admin` set.

## Troubleshooting

- **The bot does not connect:** confirm `DISCORD_TOKEN` is set and that Message
	Content Intent is enabled in the Developer Portal.
- **No response to commands:** confirm the sender's Discord ID is in `allowed`
	and that the bot can read the channel.
- **No popup or sound:** run the bot from an active graphical desktop session,
	check that the referenced files exist, and verify the system audio output.
- **`DISCORD_TOKEN environment variable not set`:** export the token in the
	same terminal used to launch `pipe.py`.

## Run automatically with systemd (example)

To start the bot automaticall we need to create
the user service directory and a private environment file:

```bash
mkdir -p /home/user/.config/systemd/user
echo 'DISCORD_TOKEN=paste-your-bot-token-here' > /home/user/.config/.env
chmod 600 /home/user/.config/.env
```

Create `/etc/systemd/user/pipe.service` with this content:

```ini
[Unit]
Description=Discord Popup Bot Service
After=default.target sound.target

[Service]
Type=simple
EnvironmentFile=/home/user/.config/.env
ExecStart=/example/path/to/your/venv/.venv/bin/python /example/path/to/your/python/pipe.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

Reload the user service manager and enable the bot:

```bash
systemctl --user daemon-reload
systemctl --user enable --now pipe.service
```

Check its status or logs with:

```bash
systemctl --user status pipe.service
journalctl --user -u pipe.service -f
```