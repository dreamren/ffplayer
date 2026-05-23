from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QStyle,
)
from PySide6.QtCore import Qt, Signal


def format_time(seconds):
    if seconds is None or seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f'{h:d}:{m:02d}:{s:02d}'
    return f'{m:02d}:{s:02d}'


class SeekSlider(QSlider):
    seek_requested = Signal(float)

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self._duration = 0
        self._seeking = False
        self.setRange(0, 10000)
        self.setValue(0)
        self.setCursor(Qt.PointingHandCursor)
        self.setSingleStep(100)
        self.setPageStep(500)

    def set_duration(self, duration):
        self._duration = max(duration, 0)

    def set_position(self, position):
        if not self._seeking and self._duration > 0:
            self.setValue(int(position / self._duration * 10000))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._seeking = True
            val = self._pos_from_event(event)
            self.setValue(val)
            self._emit_seek()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._seeking:
            val = self._pos_from_event(event)
            self.setValue(val)
            self._emit_seek()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._seeking = False
            self._emit_seek()
        super().mouseReleaseEvent(event)

    def _pos_from_event(self, event):
        ratio = event.position().x() / self.width()
        return int(max(0, min(10000, ratio * 10000)))

    def _emit_seek(self):
        if self._duration > 0:
            pos = self.value() / 10000.0 * self._duration
            self.seek_requested.emit(pos)


class VolumeSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setRange(0, 100)
        self.setValue(100)
        self.setFixedWidth(100)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            val = int(event.position().x() / self.width() * 100)
            self.setValue(max(0, min(100, val)))
        super().mousePressEvent(event)


class PlaybackControls(QWidget):
    play_toggled = Signal()
    stop_clicked = Signal()
    seek_requested = Signal(float)
    volume_changed = Signal(int)
    mute_toggled = Signal()
    fullscreen_toggled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)

        self._is_playing = False
        self._is_muted = False
        self._duration = 0

        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(32, 32)
        self.play_btn.setFocusPolicy(Qt.NoFocus)
        self.play_btn.clicked.connect(self.play_toggled)
        self._update_play_icon()

        self.stop_btn = QPushButton()
        self.stop_btn.setFixedSize(32, 32)
        self.stop_btn.setFocusPolicy(Qt.NoFocus)
        self.stop_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_btn.clicked.connect(self.stop_clicked)

        self.seek_slider = SeekSlider()
        self.seek_slider.seek_requested.connect(self.seek_requested)

        self.time_label = QLabel('00:00 / 00:00')
        self.time_label.setFixedWidth(130)
        self.time_label.setAlignment(Qt.AlignCenter)

        self.mute_btn = QPushButton()
        self.mute_btn.setFixedSize(28, 28)
        self.mute_btn.setFocusPolicy(Qt.NoFocus)
        self.mute_btn.clicked.connect(self._on_mute)
        self._update_volume_icon()

        self.volume_slider = VolumeSlider()
        self.volume_slider.valueChanged.connect(self.volume_changed)

        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.setFixedSize(28, 28)
        self.fullscreen_btn.setFocusPolicy(Qt.NoFocus)
        self.fullscreen_btn.setIcon(
            self.style().standardIcon(QStyle.SP_TitleBarMaxButton)
        )
        self.fullscreen_btn.clicked.connect(self.fullscreen_toggled)

        layout.addWidget(self.play_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.seek_slider, 1)
        layout.addWidget(self.time_label)
        layout.addWidget(self.mute_btn)
        layout.addWidget(self.volume_slider)
        layout.addWidget(self.fullscreen_btn)

    def set_playing(self, playing):
        self._is_playing = playing
        self._update_play_icon()

    def set_duration(self, duration):
        self._duration = duration
        self.seek_slider.set_duration(duration)

    def set_position(self, position):
        self.seek_slider.set_position(position)
        self.time_label.setText(
            f'{format_time(position)} / {format_time(self._duration)}'
        )

    def set_volume(self, volume):
        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(volume)
        self.volume_slider.blockSignals(False)
        self._is_muted = volume == 0
        self._update_volume_icon()

    def _update_play_icon(self):
        style = self.style()
        if self._is_playing:
            self.play_btn.setIcon(style.standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_btn.setIcon(style.standardIcon(QStyle.SP_MediaPlay))

    def _update_volume_icon(self):
        style = self.style()
        if self._is_muted:
            self.mute_btn.setIcon(style.standardIcon(QStyle.SP_MediaVolumeMuted))
        else:
            self.mute_btn.setIcon(style.standardIcon(QStyle.SP_MediaVolume))

    def _on_mute(self):
        self._is_muted = not self._is_muted
        self._update_volume_icon()
        self.mute_toggled.emit()
