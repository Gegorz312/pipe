import os
import sys
import threading
import discord
from time import sleep
import sounddevice as sd
import soundfile as sf
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QGuiApplication, QMovie, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QWidget

# --- Configuration ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

# Allowed author IDs (strings) format
example_id = "123123123123123"

audio_file_extention = ".ogg" # example .mp3 .wav .ogg .flac

# Users that can interact with bot
allowed = [example_id]
# Admins for check
admin = {example_id}

count_limit = 100

path = "/home/example/path/image_popup/"

AUDIO_CACHE = {}

# GUI class
class CinemaScreen(QWidget):

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(QGuiApplication.primaryScreen().geometry())

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, self.width(), self.height())

        self.opacity = 1.0
        self.timer = QTimer()
        self.timer.timeout.connect(self.fade)
        self.fade_delay = 15
        self.movie = None

    def start(self):
        self.opacity = 1.0
        self.setWindowOpacity(1.0)
        self.showFullScreen()

        pixmap = QPixmap(self.image_path)
        if pixmap.isNull():
            print(f"Failed to load image: {self.image_path}")
            return
        else:
            print(f"Image loaded: {self.image_path}")

        pixmap = pixmap.scaled(
            self.width(),
            self.height(),
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        self.label.setPixmap(pixmap)

        self.fade_delay = 15
        self.timer.start(30)

    def start_gif(self):
        self.opacity = 1.0
        self.setWindowOpacity(1.0)
        self.showFullScreen()

        self.movie = QMovie(self.image_path)
        if not self.movie.isValid():
            print(f"Failed to load GIF: {self.image_path}")
            return
        else:
            print(f"GIF loaded: {self.image_path}")

        self.movie.setScaledSize(self.size())
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(100)

        self.label.setMovie(self.movie)
        self.movie.start()

        # Calculate total duration manually
        total_duration = 0
        for i in range(self.movie.frameCount()):
            self.movie.jumpToFrame(i)
            total_duration += self.movie.nextFrameDelay()

        self.movie.jumpToFrame(0)
        QTimer.singleShot(total_duration, self.begin_fade_after_gif)

    def begin_fade_after_gif(self):
        self.fade_delay = 15
        self.timer.start(30)

    def fade(self):
        if self.fade_delay > 0:
            self.fade_delay -= 1
            return

        self.opacity -= 0.02
        if self.opacity <= 0:
            self.timer.stop()
            self.hide()
            return

        self.setWindowOpacity(self.opacity)

def play_sound_overlapping(sound_file):
    if sound_file not in AUDIO_CACHE:
        AUDIO_CACHE[sound_file] = sf.read(sound_file, dtype="float32")
    data, sr = AUDIO_CACHE[sound_file]

    # sd.OutputStream for independed Thread
    def stream():
        with sd.OutputStream(
            samplerate=sr,
            channels=data.shape[1] if data.ndim > 1 else 1,
            dtype="float32",
        ) as s:
            s.write(data)

    threading.Thread(target=stream, daemon=True).start()

def main():

    app = QApplication(sys.argv)
    cinema = CinemaScreen(None)

    # GUI-safe trigger helpers: schedule GUI actions on the main thread
    def trigger_popup(image_path, sound_path, count):
        for i in range(count):
            cinema.image_path = image_path
            play_sound_overlapping(sound_path)
            QTimer.singleShot(0, cinema.start)
            sleep(0.1)

    def trigger_gif_popup(gif_path, audio_gif_path, count):
        for i in range(count):
            cinema.image_path = gif_path
            play_sound_overlapping(audio_gif_path)
            QTimer.singleShot(0, cinema.start_gif)
            sleep(0.1)

    # --- Discord client setup ---
    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Bot connected as {client.user}")

    @client.event
    async def on_message(message):

        # ignore bot itself
        if message.author == client.user:
            return

        author_id = str(message.author.id)
        content = (message.content or "").strip().lower()
        content_id = int(message.id)
        channel = message.channel

        print(
            f"New Message from {message.author}: {content} random_id?:"
            f" {content_id}"
        )

        if content == "check" and admin:
            await channel.send("The adam check")

        if not allowed:
            return

        # handle commands
        try:
            content_gif = False
            content_png = False

            # checking if more then one word
            if len(content.split()) > 1:
                count = int(content.split(" ")[1])
                content = content.split(" ")[0]
                if count >= count_limit:
                    count = count_limit
            else:
                count = 1

            content_path = path + content

            if (content + ".gif") in os.listdir(path):
                content_gif = True
            elif (content + ".png") in os.listdir(path):
                content_png = True
            else:
                print("No such file: KYS")

            if content == "cinema":
                content_path_image = content_path
                content_path_audio = content_path

                if str(content_id)[-2:] == "99":
                    content_path_audio = path + "peak"
                if str(content_id)[-4:][:2] == "11":
                    content_path_image = path + "peak"

                trigger_popup(
                    content_path_image + ".png",
                    content_path_audio + audio_file_extention,
                    count,
                )
            else:
                if content_gif:
                    trigger_gif_popup(
                        content_path + ".gif", content_path + audio_file_extention, count
                    )
                elif content_png:
                    trigger_popup(
                        content_path + ".png", content_path + audio_file_extention, count
                    )

        except Exception as e:
            print(f"Error handling command: {e}")

    # Start Discord client in a background thread
    if not DISCORD_TOKEN:
        print(
            "DISCORD_TOKEN environment variable not set. Set it and restart."
        )
    else:

        def run_discord():
            try:
                client.run(DISCORD_TOKEN)
            except Exception as e:
                print(f"Discord client error: {e}")

        threading.Thread(target=run_discord, daemon=True).start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()