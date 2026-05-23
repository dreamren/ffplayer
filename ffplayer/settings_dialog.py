from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDialogButtonBox,
    QGroupBox,
    QVBoxLayout,
    QFileDialog,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
)
from ffplayer.config import SIZE_MODE_LABELS


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle('设置')
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        playback_group = QGroupBox('播放')
        playback_layout = QFormLayout()

        self.size_combo = QComboBox()
        self.size_combo.addItems(SIZE_MODE_LABELS)
        self.size_combo.setCurrentIndex(config.window_size_mode)
        playback_layout.addRow('默认窗口大小:', self.size_combo)

        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setValue(config.default_volume)
        self.volume_spin.setSuffix(' %')
        playback_layout.addRow('默认音量:', self.volume_spin)

        self.remember_playback_cb = QCheckBox('记住上次播放位置')
        self.remember_playback_cb.setChecked(config.remember_playback_position)
        playback_layout.addRow(self.remember_playback_cb)

        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)

        window_group = QGroupBox('窗口')
        window_layout = QFormLayout()

        self.remember_pos_cb = QCheckBox('记住窗口位置')
        self.remember_pos_cb.setChecked(config.remember_position)
        window_layout.addRow(self.remember_pos_cb)

        self.always_on_top_cb = QCheckBox('窗口置顶')
        self.always_on_top_cb.setChecked(config.always_on_top)
        window_layout.addRow(self.always_on_top_cb)

        window_group.setLayout(window_layout)
        layout.addWidget(window_group)

        screenshot_group = QGroupBox('截图')
        screenshot_layout = QHBoxLayout()

        self.screenshot_dir_edit = QLineEdit(config.screenshot_dir)
        self.screenshot_dir_edit.setPlaceholderText('默认: 临时目录')
        screenshot_layout.addWidget(self.screenshot_dir_edit)

        browse_btn = QPushButton('浏览...')
        browse_btn.clicked.connect(self._browse_screenshot_dir)
        screenshot_layout.addWidget(browse_btn)

        screenshot_group.setLayout(screenshot_layout)
        layout.addWidget(screenshot_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText('确定')
        buttons.button(QDialogButtonBox.Cancel).setText('取消')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_screenshot_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, '选择截图保存目录')
        if dir_path:
            self.screenshot_dir_edit.setText(dir_path)

    def get_settings(self):
        return {
            'window_size_mode': self.size_combo.currentIndex(),
            'default_volume': self.volume_spin.value(),
            'remember_position': self.remember_pos_cb.isChecked(),
            'always_on_top': self.always_on_top_cb.isChecked(),
            'screenshot_dir': self.screenshot_dir_edit.text(),
            'remember_playback_position': self.remember_playback_cb.isChecked(),
        }
