import sys
import os
import shutil


def main():
    ffplay_name = 'ffplay.exe' if sys.platform == 'win32' else 'ffplay'
    ffplay_found = shutil.which(ffplay_name) is not None

    if not ffplay_found:
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ffplay_path = os.path.join(base, ffplay_name)
        if not os.path.isfile(ffplay_path):
            print(
                'Error: ffplay not found!\n\n'
                'Please put ffplay.exe (and ffprobe.exe, ffmpeg.exe) in:\n'
                f'  {base}\n\n'
                'Or add them to your system PATH.\n\n'
                'Download from: https://ffmpeg.org/download.html\n'
                '  - Windows ARM64: https://github.com/BtbN/FFmpeg-Builds/releases\n'
                '  - Windows x64: https://www.gyan.dev/ffmpeg/builds/'
            )
            sys.exit(1)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt

    app = QApplication(sys.argv)
    app.setApplicationName('FFPlayer')
    app.setOrganizationName('FFPlayer')
    app.setStyle('Fusion')

    from ffplayer.config import Config
    from ffplayer.main_window import MainWindow

    config = Config()
    window = MainWindow(config)
    window.show()

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if os.path.isfile(filepath):
            window._play_file(filepath)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
