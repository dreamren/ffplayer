from PySide6.QtCore import QSettings

WINDOW_SIZE_ORIGINAL = 0
WINDOW_SIZE_HALF = 1
WINDOW_SIZE_QUARTER = 2
WINDOW_SIZE_DOUBLE = 3
WINDOW_SIZE_FIT_SCREEN = 4

SIZE_MODE_LABELS = ['原始大小', '1/2', '1/4', '2倍', '适应屏幕']

SIZE_MODE_FACTORS = {
    WINDOW_SIZE_ORIGINAL: 1.0,
    WINDOW_SIZE_HALF: 0.5,
    WINDOW_SIZE_QUARTER: 0.25,
    WINDOW_SIZE_DOUBLE: 2.0,
    WINDOW_SIZE_FIT_SCREEN: -1,
}


class Config:
    def __init__(self):
        self._settings = QSettings('FFPlayer', 'FFPlayer')

    @property
    def window_size_mode(self):
        return self._settings.value('window_size_mode', 0, type=int)

    @window_size_mode.setter
    def window_size_mode(self, value):
        self._settings.setValue('window_size_mode', value)

    @property
    def window_pos(self):
        pos = self._settings.value('window_pos', None)
        if pos and isinstance(pos, (list, tuple)) and len(pos) == 2:
            return tuple(int(p) for p in pos)
        return None

    @window_pos.setter
    def window_pos(self, pos):
        if pos:
            self._settings.setValue('window_pos', list(pos))
        else:
            self._settings.remove('window_pos')

    @property
    def window_size(self):
        size = self._settings.value('window_size', None)
        if size and isinstance(size, (list, tuple)) and len(size) == 2:
            return tuple(int(s) for s in size)
        return None

    @window_size.setter
    def window_size(self, size):
        if size:
            self._settings.setValue('window_size', list(size))
        else:
            self._settings.remove('window_size')

    @property
    def remember_position(self):
        return self._settings.value('remember_position', True, type=bool)

    @remember_position.setter
    def remember_position(self, value):
        self._settings.setValue('remember_position', value)

    @property
    def default_volume(self):
        return self._settings.value('default_volume', 100, type=int)

    @default_volume.setter
    def default_volume(self, value):
        self._settings.setValue('default_volume', value)

    @property
    def last_open_dir(self):
        return self._settings.value('last_open_dir', '')

    @last_open_dir.setter
    def last_open_dir(self, value):
        self._settings.setValue('last_open_dir', value)

    @property
    def recent_files(self):
        val = self._settings.value('recent_files', [])
        if isinstance(val, str):
            return []
        return val

    @recent_files.setter
    def recent_files(self, value):
        self._settings.setValue('recent_files', value)

    @property
    def screenshot_dir(self):
        return self._settings.value('screenshot_dir', '')

    @screenshot_dir.setter
    def screenshot_dir(self, value):
        self._settings.setValue('screenshot_dir', value)

    @property
    def always_on_top(self):
        return self._settings.value('always_on_top', False, type=bool)

    @always_on_top.setter
    def always_on_top(self, value):
        self._settings.setValue('always_on_top', value)

    @property
    def last_file(self):
        return self._settings.value('last_file', '')

    @last_file.setter
    def last_file(self, value):
        self._settings.setValue('last_file', value)

    @property
    def remember_playback_position(self):
        return self._settings.value('remember_playback_position', True, type=bool)

    @remember_playback_position.setter
    def remember_playback_position(self, value):
        self._settings.setValue('remember_playback_position', value)

    @property
    def last_playback_position(self):
        return self._settings.value('last_playback_position', 0.0, type=float)

    @last_playback_position.setter
    def last_playback_position(self, value):
        self._settings.setValue('last_playback_position', value)

    @property
    def last_playback_file(self):
        return self._settings.value('last_playback_file', '')

    @last_playback_file.setter
    def last_playback_file(self, value):
        self._settings.setValue('last_playback_file', value)
