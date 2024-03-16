import sys
from yt_dlp import YoutubeDL
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QRadioButton, QLineEdit,
    QPushButton, QProgressBar, QSpacerItem, QSizePolicy, QTextEdit
)
import argparse
from pathlib import Path
from .settings import default_download_location


def get_params(audio=False):
    if audio:
        return {
            'final_ext':
                'mp3',
            'format':
                'bestaudio/best',
            'outtmpl':
                {
                    'default': f'{default_download_location}\\%(title)s.%(ext)s'
                },
            'postprocessors':
                [
                    {
                        'key': 'FFmpegExtractAudio',
                        'nopostoverwrites': False,
                        'preferredcodec': 'mp3',
                        'preferredquality': '192'
                    }
                ]
        }
    else:
        return {
            'final_ext': 'mp4',
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'outtmpl':
                {
                    'default': f'{default_download_location}\\%(title)s.%(ext)s'
                },
            'postprocessors':
                [
                    {
                        'key': 'FFmpegVideoRemuxer',
                        'preferedformat': 'mp4'
                    }, {
                        'already_have_subtitle': True,
                        'key': 'FFmpegEmbedSubtitle'
                    }
                ],
            'subtitlesformat': 'srt',
            'subtitleslangs': ['en'],
            'writesubtitles': True
        }


class WorkerThread(QThread):
    progress_updated = pyqtSignal(int)

    def __init__(self, urls, audio: bool = False):
        super().__init__()
        self.urls = urls
        self.audio = audio

    def run(self):
        # Simulate work with a timer
        params = get_params(audio=self.audio)

        n_done = 0
        self.progress_updated.emit(n_done)

        def progress_hook(d):
            nonlocal n_done
            if d['status'] == 'finished':
                n_done += 1
                self.progress_updated.emit(n_done)

        params['progress_hooks'] = [progress_hook]
        params["postprocessor_hooks"] = [progress_hook]
        with YoutubeDL(params=params) as ydl:
            ydl.download(self.urls)


class URLInputWidget(QWidget):
    def __init__(self, initial_text=""):
        super().__init__()
        self.initUI(initial_text=initial_text)

    def initUI(self, initial_text=""):
        # Main layout
        self.mainLayout = QVBoxLayout()
        self.setLayout(self.mainLayout)
        self.resize(800, 600)

        # Radio buttons for "audio" and "video"
        self.audioButton = QRadioButton("Audio")
        self.videoButton = QRadioButton("Video")
        self.videoButton.setChecked(True)  # Default to "video"
        radioLayout = QHBoxLayout()
        radioLayout.addWidget(self.audioButton)
        radioLayout.addWidget(self.videoButton)
        self.mainLayout.addLayout(radioLayout)

        # Multi-line text box for URLs
        self.urlTextEdit = QTextEdit()
        self.urlTextEdit.setPlaceholderText("Enter URLs, one per line")
        self.urlTextEdit.setAcceptRichText(False)
        self.urlTextEdit.insertPlainText(initial_text)

        self.mainLayout.addWidget(self.urlTextEdit)

        # Button to process URLs
        self.downloadButton = QPushButton("Download")
        self.downloadButton.clicked.connect(self.download)
        self.mainLayout.addWidget(self.downloadButton)

        self.progress = QProgressBar()
        self.mainLayout.addWidget(self.progress)
        self.progress.setHidden(True)

    def download(self):
        urls = [
            stripped_line for stripped_line in (
                line.strip()
                for line in self.urlTextEdit.toPlainText().splitlines()
            ) if len(stripped_line) > 0
        ]
        self.urlTextEdit.setEnabled(False)
        self.downloadButton.setEnabled(False)
        self.audioButton.setEnabled(False)
        self.videoButton.setEnabled(False)
        self.progress.setHidden(False)
        # 1 for download, 1 for postprocessing, per url
        self.progress.setMaximum(len(urls) * 2)
        self.progress.setValue(0)

        audio = self.audioButton.isChecked()

        self.worker_thread = WorkerThread(urls=urls, audio=audio)
        self.worker_thread.progress_updated.connect(self.progress.setValue)
        self.worker_thread.start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs="?", default=None)
    parsed_args = parser.parse_args(sys.argv[1:])

    app = QApplication([])
    ex = URLInputWidget(
        initial_text=Path(parsed_args.file).read_text() if parsed_args.
        file is not None else ""
    )
    ex.show()
    sys.exit(app.exec_())
