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
                '错误：未找到 ffplay！\n\n'
                '请将 ffplay.exe（以及 ffprobe.exe、ffmpeg.exe）放在：\n'
                f'  {base}\n\n'
                '或添加到系统 PATH。\n\n'
                '下载地址: https://ffmpeg.org/download.html\n'
                '  - Windows ARM64: https://github.com/BtbN/FFmpeg-Builds/releases\n'
                '  - Windows x64: https://www.gyan.dev/ffmpeg/builds/'
            )
            sys.exit(1)

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName('FFPlayer')
    app.setOrganizationName('FFPlayer')

    from ffplayer.styles import DARK_STYLE
    app.setStyleSheet(DARK_STYLE)

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
