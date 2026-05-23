import os
import sys
import time
import re
import subprocess
import threading
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QTimer


class FFPlayWidget(QWidget):
    time_changed = Signal(float)
    duration_changed = Signal(float)
    state_changed = Signal(str)
    video_size_changed = Signal(int, int)
    eof_reached = Signal()
    error_occurred = Signal(str)

    VK_LEFT = 0x25
    VK_UP = 0x26
    VK_RIGHT = 0x27
    VK_DOWN = 0x28
    VK_SPACE = 0x20
    VK_9 = 0x39
    VK_0 = 0x30
    VK_M = 0x4D
    VK_F = 0x46
    VK_PGDN = 0x22
    VK_PGUP = 0x21

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 180)
        self._process = None
        self._ffplay_path = self._find_binary('ffplay')
        self._ffprobe_path = self._find_binary('ffprobe')
        self._ffmpeg_path = self._find_binary('ffmpeg')
        self._current_file = ''
        self._duration = 0
        self._position = 0
        self._is_paused = False
        self._volume = 100
        self._speed = 1.0
        self._start_time = 0
        self._start_position = 0
        self._ffplay_hwnd = None
        self._video_width = 0
        self._video_height = 0
        self._seeking = False
        self._running = False
        self._embed_retries = 0
        self._pending_pause = False
        self._stderr_lines = []

        self._position_timer = QTimer(self)
        self._position_timer.setInterval(200)
        self._position_timer.timeout.connect(self._update_position)

        self._monitor_timer = QTimer(self)
        self._monitor_timer.setInterval(500)
        self._monitor_timer.timeout.connect(self._monitor_process)

    @staticmethod
    def _find_binary(name):
        if sys.platform == 'win32':
            name += '.exe'
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
            full = os.path.join(base, name)
            if os.path.isfile(full):
                return full
        for path in os.environ.get('PATH', '').split(os.pathsep):
            full = os.path.join(path.strip(), name)
            if os.path.isfile(full):
                return full
        return name

    def _get_video_info(self, filepath):
        try:
            cmd = [
                self._ffprobe_path,
                '-v', 'error',
                '-show_entries',
                'format=duration:stream=width,height',
                '-of', 'default=noprint_wrappers=1',
                filepath,
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10
            )
            duration = 0.0
            width = 0
            height = 0
            for line in result.stdout.strip().split('\n'):
                if line.startswith('duration='):
                    try:
                        duration = float(line.split('=', 1)[1])
                    except (ValueError, IndexError):
                        pass
                elif line.startswith('width='):
                    try:
                        width = int(line.split('=', 1)[1])
                    except (ValueError, IndexError):
                        pass
                elif line.startswith('height='):
                    try:
                        height = int(line.split('=', 1)[1])
                    except (ValueError, IndexError):
                        pass
            return duration, width, height
        except Exception:
            return 0.0, 0, 0

    def play(self, filepath):
        self.stop()
        self._current_file = filepath
        self._position = 0
        self._is_paused = False

        duration, width, height = self._get_video_info(filepath)
        self._duration = duration
        if width and height:
            self._video_width = width
            self._video_height = height
            self.video_size_changed.emit(width, height)
        if duration > 0:
            self.duration_changed.emit(duration)

        self._start_ffplay(filepath, 0)

    def _build_atempo_chain(self, speed):
        if abs(speed - 1.0) < 0.01:
            return None
        filters = []
        remaining = speed
        while remaining < 0.5:
            filters.append('atempo=0.5')
            remaining /= 0.5
        while remaining > 2.0:
            filters.append('atempo=2.0')
            remaining /= 2.0
        filters.append(f'atempo={remaining:.4f}')
        return ','.join(filters)

    def _start_ffplay(self, filepath, start_position=0):
        self._seeking = True
        self._kill_process()

        window_title = f'FFPlayer_Video_{os.getpid()}'

        cmd = [
            self._ffplay_path,
            '-noborder',
            '-window_title', window_title,
            '-autoexit',
            '-stats',
            '-volume', str(self._volume),
            '-x', str(max(320, self.width())),
            '-y', str(max(180, self.height())),
        ]

        if start_position > 0:
            cmd.extend(['-ss', f'{start_position:.3f}'])

        atempo = self._build_atempo_chain(self._speed)
        if atempo:
            cmd.extend(['-af', atempo])
            setpts = 1.0 / self._speed
            cmd.extend(['-vf', f'setpts={setpts:.4f}*PTS'])

        cmd.append(filepath)

        try:
            kwargs = {
                'stderr': subprocess.PIPE,
                'stdout': subprocess.DEVNULL,
                'stdin': subprocess.DEVNULL,
            }
            if sys.platform == 'win32':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            self._process = subprocess.Popen(cmd, **kwargs)
        except FileNotFoundError:
            self.error_occurred.emit(
                '未找到 ffplay！请将 ffplay.exe 放在程序目录或系统 PATH 中。'
            )
            self._seeking = False
            return
        except Exception as e:
            self.error_occurred.emit(f'启动 ffplay 失败: {e}')
            self._seeking = False
            return

        self._start_position = start_position
        self._start_time = time.time()
        self._running = True
        self._ffplay_hwnd = None
        self._embed_retries = 0
        self._pending_pause = self._is_paused
        self._stderr_lines = []

        self._stderr_thread = threading.Thread(
            target=self._parse_stderr, daemon=True
        )
        self._stderr_thread.start()

        QTimer.singleShot(200, self._try_embed_window)

        self._position_timer.start()
        self._monitor_timer.start()
        self.state_changed.emit('playing')
        self._seeking = False

    def _kill_process(self):
        self._running = False
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
                try:
                    self._process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
        self._process = None
        self._ffplay_hwnd = None

    def _parse_stderr(self):
        if not self._process or not self._process.stderr:
            return
        try:
            while self._running and self._process.poll() is None:
                line = self._process.stderr.readline()
                if not line:
                    break
                try:
                    text = line.decode('utf-8', errors='ignore').strip()
                except Exception:
                    continue
                if not text:
                    continue
                self._stderr_lines.append(text)
                match = re.search(r'time=(\d+:\d+:\d+\.\d+)', text)
                if match:
                    time_str = match.group(1)
                    parts = time_str.split(':')
                    if len(parts) == 3:
                        try:
                            h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
                            pos = h * 3600 + m * 60 + s
                            self._position = pos
                            self.time_changed.emit(pos)
                        except (ValueError, IndexError):
                            pass
        except Exception:
            pass

    def _try_embed_window(self):
        if sys.platform != 'win32':
            return
        if not self._running or not self._process or self._process.poll() is not None:
            return

        try:
            import ctypes
            user32 = ctypes.windll.user32

            window_title = f'FFPlayer_Video_{os.getpid()}'
            hwnd = user32.FindWindowW(None, window_title)

            if not hwnd:
                self._embed_retries += 1
                if self._embed_retries < 25:
                    QTimer.singleShot(150, self._try_embed_window)
                return

            self._ffplay_hwnd = hwnd
            qt_hwnd = int(self.winId())

            user32.SetParent(hwnd, qt_hwnd)

            GWL_STYLE = -16
            WS_CHILD = 0x40000000
            WS_VISIBLE = 0x10000000
            WS_CAPTION = 0x00C00000
            WS_THICKFRAME = 0x00040000
            WS_SYSMENU = 0x00080000
            WS_MINIMIZEBOX = 0x00020000
            WS_MAXIMIZEBOX = 0x00010000

            current_style = user32.GetWindowLongW(hwnd, GWL_STYLE)
            new_style = current_style & ~(
                WS_CAPTION
                | WS_THICKFRAME
                | WS_SYSMENU
                | WS_MINIMIZEBOX
                | WS_MAXIMIZEBOX
            )
            new_style |= WS_CHILD | WS_VISIBLE
            user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)

            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_NOACTIVATE = 0x08000000
            current_exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(
                hwnd,
                GWL_EXSTYLE,
                (current_exstyle & ~WS_EX_APPWINDOW) | WS_EX_NOACTIVATE,
            )

            self._resize_ffplay()

            if self._pending_pause:
                QTimer.singleShot(300, self._apply_pending_pause)

        except Exception:
            pass

    def _apply_pending_pause(self):
        if self._ffplay_hwnd:
            self._send_key(self.VK_SPACE)
        self._pending_pause = False

    def _resize_ffplay(self):
        if not self._ffplay_hwnd or sys.platform != 'win32':
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            w = self.width()
            h = self.height()
            user32.MoveWindow(self._ffplay_hwnd, 0, 0, w, h, True)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_ffplay()

    def _update_position(self):
        if self._is_paused or self._seeking:
            return
        if self._duration > 0 and self._position < self._duration:
            elapsed = time.time() - self._start_time
            approx_pos = self._start_position + elapsed * self._speed
            if abs(approx_pos - self._position) > 0.5:
                self._position = min(approx_pos, self._duration)
                self.time_changed.emit(self._position)

    def _monitor_process(self):
        if self._process and self._process.poll() is not None:
            exit_code = self._process.poll()
            self._running = False
            self._position_timer.stop()
            self._monitor_timer.stop()
            if exit_code == 0:
                self.eof_reached.emit()
            elif exit_code != 0 and self._stderr_lines:
                last_lines = self._stderr_lines[-5:]
                err_msg = '\n'.join(last_lines)
                if 'No such file' in err_msg or 'Permission denied' in err_msg:
                    self.error_occurred.emit(err_msg[:200])
            self.state_changed.emit('paused')

    def _send_key(self, vk_code):
        if not self._ffplay_hwnd or sys.platform != 'win32':
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            WM_KEYDOWN = 0x0100
            WM_KEYUP = 0x0101
            user32.PostMessageW(self._ffplay_hwnd, WM_KEYDOWN, vk_code, 0)
            user32.PostMessageW(self._ffplay_hwnd, WM_KEYUP, vk_code, 0xC0000001)
        except Exception:
            pass

    def pause(self):
        if not self._current_file:
            return
        self._send_key(self.VK_SPACE)
        self._is_paused = not self._is_paused
        if self._is_paused:
            self.state_changed.emit('paused')
        else:
            self._start_time = time.time()
            self.state_changed.emit('playing')

    def set_pause(self, paused):
        if paused != self._is_paused:
            self.pause()

    def seek(self, position):
        if not self._current_file:
            return
        self._position = max(0, position)
        self._start_ffplay(self._current_file, self._position)
        self._is_paused = False

    def relative_seek(self, offset):
        if not self._ffplay_hwnd or not self._current_file:
            return
        if offset > 0:
            if offset <= 10:
                self._send_key(self.VK_RIGHT)
            elif offset <= 60:
                self._send_key(self.VK_DOWN)
            else:
                self._send_key(self.VK_PGDN)
        elif offset < 0:
            if offset >= -10:
                self._send_key(self.VK_LEFT)
            elif offset >= -60:
                self._send_key(self.VK_UP)
            else:
                self._send_key(self.VK_PGUP)

    def seek_toward(self, target_position):
        if not self._ffplay_hwnd or not self._current_file or self._duration <= 0:
            return
        target = max(0, min(self._duration, target_position))
        diff = target - self._position
        if abs(diff) < 1:
            return
        if diff > 0:
            if diff <= 10:
                self._send_key(self.VK_RIGHT)
                self._position += 10
            elif diff <= 60:
                self._send_key(self.VK_DOWN)
                self._position += 60
            else:
                self._send_key(self.VK_PGDN)
                self._position += 600
        else:
            if diff >= -10:
                self._send_key(self.VK_LEFT)
                self._position -= 10
            elif diff >= -60:
                self._send_key(self.VK_UP)
                self._position -= 60
            else:
                self._send_key(self.VK_PGUP)
                self._position -= 600
        self._position = max(0, min(self._duration, self._position))

    def stop(self):
        self._kill_process()
        self._position_timer.stop()
        self._monitor_timer.stop()
        self._position = 0
        self._is_paused = True
        self.state_changed.emit('paused')

    @property
    def is_paused(self):
        return self._is_paused

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        old_vol = self._volume
        self._volume = max(0, min(100, int(value)))
        if self._ffplay_hwnd and sys.platform == 'win32' and old_vol != self._volume:
            diff = self._volume - old_vol
            if diff > 0:
                steps = max(1, diff // 2)
                for _ in range(steps):
                    self._send_key(self.VK_0)
            elif diff < 0:
                steps = max(1, abs(diff) // 2)
                for _ in range(steps):
                    self._send_key(self.VK_9)

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = max(0.25, min(4.0, round(value, 2)))
        if self._current_file and self._running:
            self._start_ffplay(self._current_file, self._position)
            self._is_paused = False

    def screenshot(self, path=''):
        if not self._current_file:
            return
        if not path:
            import tempfile
            base_dir = tempfile.gettempdir()
            path = os.path.join(
                base_dir, f'ffplayer_screenshot_{int(time.time())}.png'
            )
        cmd = [
            self._ffmpeg_path,
            '-y',
            '-ss', f'{self._position:.3f}',
            '-i', self._current_file,
            '-frames:v', '1',
            '-q:v', '2',
            path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=10)
        except Exception:
            pass

    @property
    def media_title(self):
        if self._current_file:
            return os.path.basename(self._current_file)
        return ''

    @property
    def time_pos(self):
        return self._position

    def close_player(self):
        self.stop()
