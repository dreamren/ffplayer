import os
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QFileDialog,
    QMessageBox,
    QInputDialog,
    QMenu,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QAction

from ffplayer.ffplay_widget import FFPlayWidget
from ffplayer.controls import PlaybackControls
from ffplayer.settings_dialog import SettingsDialog
from ffplayer.styles import DARK_STYLE
from ffplayer.config import (
    Config,
    WINDOW_SIZE_ORIGINAL,
    WINDOW_SIZE_HALF,
    WINDOW_SIZE_QUARTER,
    WINDOW_SIZE_DOUBLE,
    WINDOW_SIZE_FIT_SCREEN,
    SIZE_MODE_LABELS,
    SIZE_MODE_FACTORS,
)


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._is_fullscreen = False
        self._video_width = 0
        self._video_height = 0
        self._current_file = ''
        self._pre_mute_volume = 100
        self._controls_visible = True
        self._fullscreen_hide_timer = QTimer(self)
        self._fullscreen_hide_timer.setSingleShot(True)
        self._fullscreen_hide_timer.setInterval(3000)
        self._fullscreen_hide_timer.timeout.connect(self._auto_hide_controls)

        self.setWindowTitle('FFPlayer')
        self.setMinimumSize(480, 320)
        self.setStyleSheet(DARK_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.video = FFPlayWidget()
        layout.addWidget(self.video, 1)

        self.controls = PlaybackControls()
        layout.addWidget(self.controls)

        self.video.time_changed.connect(self.controls.set_position)
        self.video.duration_changed.connect(self._on_duration)
        self.video.state_changed.connect(self._on_state_changed)
        self.video.video_size_changed.connect(self._on_video_size)
        self.video.eof_reached.connect(self._on_eof)
        self.video.error_occurred.connect(self._on_error)
        self.controls.play_toggled.connect(self._toggle_play)
        self.controls.stop_clicked.connect(self._stop)
        self.controls.seek_requested.connect(self.video.seek)
        self.controls.seek_drag_started.connect(self.video.start_drag_seek)
        self.controls.seek_drag_moved.connect(self.video.update_drag_seek)
        self.controls.seek_drag_ended.connect(self.video.end_drag_seek)
        self.controls.volume_changed.connect(self._set_volume)
        self.controls.mute_toggled.connect(self._toggle_mute)
        self.controls.fullscreen_toggled.connect(self._toggle_fullscreen)

        self._create_menus()

        self.statusBar().showMessage('就绪 — 拖放文件或按 Ctrl+O 打开')

        self.setAcceptDrops(True)

        self.controls.set_volume(config.default_volume)
        self.video._volume = config.default_volume

        if config.always_on_top:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self._restore_window_state()

    def _create_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('文件(&F)')

        open_action = QAction('打开文件...(&O)', self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        open_url_action = QAction('打开网址...(&U)', self)
        open_url_action.setShortcut(QKeySequence('Ctrl+U'))
        open_url_action.triggered.connect(self._open_url)
        file_menu.addAction(open_url_action)

        self.recent_menu = file_menu.addMenu('最近文件(&R)')
        self._update_recent_menu()

        file_menu.addSeparator()

        screenshot_action = QAction('截图(&S)', self)
        screenshot_action.setShortcut(QKeySequence('Ctrl+S'))
        screenshot_action.triggered.connect(self._screenshot)
        file_menu.addAction(screenshot_action)

        file_menu.addSeparator()

        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        playback_menu = menubar.addMenu('播放(&P)')

        play_pause_action = QAction('播放/暂停(&Space)', self)
        play_pause_action.setShortcut(QKeySequence('Space'))
        play_pause_action.triggered.connect(self._toggle_play)
        playback_menu.addAction(play_pause_action)

        stop_action = QAction('停止(&T)', self)
        stop_action.triggered.connect(self._stop)
        playback_menu.addAction(stop_action)

        playback_menu.addSeparator()

        seek_fwd_action = QAction('快进 5秒(&Right)', self)
        seek_fwd_action.setShortcut(QKeySequence('Right'))
        seek_fwd_action.triggered.connect(lambda: self.video.relative_seek(5))
        playback_menu.addAction(seek_fwd_action)

        seek_back_action = QAction('快退 5秒(&Left)', self)
        seek_back_action.setShortcut(QKeySequence('Left'))
        seek_back_action.triggered.connect(lambda: self.video.relative_seek(-5))
        playback_menu.addAction(seek_back_action)

        seek_fwd_long_action = QAction('快进 30秒', self)
        seek_fwd_long_action.setShortcut(QKeySequence('Shift+Right'))
        seek_fwd_long_action.triggered.connect(
            lambda: self.video.relative_seek(30)
        )
        playback_menu.addAction(seek_fwd_long_action)

        seek_back_long_action = QAction('快退 30秒', self)
        seek_back_long_action.setShortcut(QKeySequence('Shift+Left'))
        seek_back_long_action.triggered.connect(
            lambda: self.video.relative_seek(-30)
        )
        playback_menu.addAction(seek_back_long_action)

        playback_menu.addSeparator()

        speed_up_action = QAction('加速 +0.25x', self)
        speed_up_action.setShortcut(QKeySequence(']'))
        speed_up_action.triggered.connect(lambda: self._change_speed(0.25))
        playback_menu.addAction(speed_up_action)

        speed_down_action = QAction('减速 -0.25x', self)
        speed_down_action.setShortcut(QKeySequence('['))
        speed_down_action.triggered.connect(lambda: self._change_speed(-0.25))
        playback_menu.addAction(speed_down_action)

        speed_reset_action = QAction('重置速度 1.0x', self)
        speed_reset_action.setShortcut(QKeySequence('\\'))
        speed_reset_action.triggered.connect(lambda: self._set_speed(1.0))
        playback_menu.addAction(speed_reset_action)

        view_menu = menubar.addMenu('视图(&V)')

        fullscreen_action = QAction('全屏(&F)', self)
        fullscreen_action.setShortcut(QKeySequence('F'))
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        view_menu.addSeparator()

        size_group_menu = view_menu.addMenu('窗口大小')
        for i, label in enumerate(SIZE_MODE_LABELS):
            action = QAction(label, self)
            action.triggered.connect(
                lambda checked, idx=i: self._set_window_size_mode(idx)
            )
            size_group_menu.addAction(action)

        view_menu.addSeparator()

        self.on_top_action = QAction('窗口置顶(&T)', self)
        self.on_top_action.setCheckable(True)
        self.on_top_action.setChecked(self.config.always_on_top)
        self.on_top_action.triggered.connect(self._toggle_always_on_top)
        view_menu.addAction(self.on_top_action)

        settings_menu = menubar.addMenu('设置(&S)')

        prefs_action = QAction('首选项...(&P)', self)
        prefs_action.triggered.connect(self._show_settings)
        settings_menu.addAction(prefs_action)

        help_menu = menubar.addMenu('帮助(&H)')

        about_action = QAction('关于 FFPlayer(&A)', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        shortcuts_action = QAction('快捷键(&K)', self)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)

    def _restore_window_state(self):
        if self.config.remember_position and self.config.window_pos:
            self.move(*self.config.window_pos)
        if self.config.window_size:
            self.resize(*self.config.window_size)

    def _save_window_state(self):
        if self.config.remember_position:
            self.config.window_pos = (self.pos().x(), self.pos().y())
        self.config.window_size = (self.width(), self.height())

    def _open_file(self):
        dir_path = self.config.last_open_dir or ''
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '打开视频',
            dir_path,
            '视频文件 (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.ts '
            '*.m4v *.3gp *.mpg *.mpeg *.vob *.ogv *.rm *.rmvb *.m2ts);;'
            '音频文件 (*.mp3 *.flac *.wav *.ogg *.aac *.m4a *.wma *.opus);;'
            '所有文件 (*)',
        )
        if file_path:
            self._play_file(file_path)
            self.config.last_open_dir = os.path.dirname(file_path)

    def _open_url(self):
        url, ok = QInputDialog.getText(self, '打开网址', '输入视频网址:')
        if ok and url.strip():
            self._play_file(url.strip())

    def _play_file(self, filepath):
        self._save_playback_position()
        self._current_file = filepath
        self.video.play(filepath)
        display_name = (
            os.path.basename(filepath)
            if os.path.isfile(filepath)
            else filepath
        )
        self.setWindowTitle(f'FFPlayer - {display_name}')
        self._add_recent_file(filepath)
        self.controls.set_playing(True)
        self.config.last_file = filepath
        self.config.last_playback_file = filepath
        self.statusBar().showMessage(f'正在播放: {filepath}')

    def _add_recent_file(self, filepath):
        recent = list(self.config.recent_files)
        if filepath in recent:
            recent.remove(filepath)
        recent.insert(0, filepath)
        recent = recent[:10]
        self.config.recent_files = recent
        self._update_recent_menu()

    def _update_recent_menu(self):
        self.recent_menu.clear()
        recent = self.config.recent_files
        if not recent:
            empty_action = self.recent_menu.addAction('无最近文件')
            empty_action.setEnabled(False)
            return
        for filepath in recent:
            display = os.path.basename(filepath)
            action = self.recent_menu.addAction(display)
            action.setToolTip(filepath)
            action.triggered.connect(
                lambda checked, f=filepath: self._play_file(f)
            )

    def _toggle_play(self):
        if self._current_file:
            self.video.pause()
        else:
            self._open_file()

    def _stop(self):
        self._save_playback_position()
        self.video.stop()
        self.controls.set_playing(False)
        self.setWindowTitle('FFPlayer')
        self.statusBar().showMessage('已停止')

    def _change_speed(self, delta):
        new_speed = round(max(0.25, min(4.0, self.video.speed + delta)), 2)
        self.video.speed = new_speed
        self.statusBar().showMessage(f'播放速度: {new_speed:.2f}x')

    def _set_speed(self, speed):
        self.video.speed = speed
        self.statusBar().showMessage(f'播放速度: {speed:.2f}x')

    def _set_volume(self, volume):
        self.video.volume = volume
        self._pre_mute_volume = volume if volume > 0 else self._pre_mute_volume
        self.config.default_volume = volume

    def _toggle_mute(self):
        if self.video.volume > 0:
            self._pre_mute_volume = int(self.video.volume)
            self.video.volume = 0
            self.controls.set_volume(0)
        else:
            self.video.volume = self._pre_mute_volume
            self.controls.set_volume(self._pre_mute_volume)

    def _toggle_fullscreen(self):
        if self._is_fullscreen:
            self.showNormal()
            self.menuBar().show()
            self.controls.show()
            self._is_fullscreen = False
            self._fullscreen_hide_timer.stop()
        else:
            self.menuBar().hide()
            self.controls.show()
            self.showFullScreen()
            self._is_fullscreen = True
            self._fullscreen_hide_timer.start()

    def _auto_hide_controls(self):
        if self._is_fullscreen:
            self.controls.hide()
            self._controls_visible = False

    def _toggle_always_on_top(self):
        on_top = self.on_top_action.isChecked()
        self.config.always_on_top = on_top
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, on_top)
        if was_visible:
            self.show()

    def _set_window_size_mode(self, mode):
        self.config.window_size_mode = mode
        if self._video_width > 0 and self._video_height > 0:
            self._apply_window_size(mode)

    def _apply_window_size(self, mode):
        if self._video_width <= 0 or self._video_height <= 0:
            return

        w, h = self._video_width, self._video_height

        if mode == WINDOW_SIZE_FIT_SCREEN:
            screen = self.screen()
            if screen:
                avail = screen.availableGeometry()
                max_w = avail.width() - 40
                max_h = avail.height() - 120
                ratio = min(max_w / w, max_h / h)
                target_w = int(w * ratio)
                target_h = int(h * ratio)
            else:
                target_w, target_h = w, h
        else:
            factor = SIZE_MODE_FACTORS.get(mode, 1.0)
            target_w = int(w * factor)
            target_h = int(h * factor)

        current_w = self.video.width()
        current_h = self.video.height()
        dw = target_w - current_w
        dh = target_h - current_h
        if dw != 0 or dh != 0:
            self.resize(self.width() + dw, self.height() + dh)

    def _on_duration(self, duration):
        self.controls.set_duration(duration)

    def _on_state_changed(self, state):
        self.controls.set_playing(state == 'playing')

    def _on_video_size(self, width, height):
        self._video_width = width
        self._video_height = height
        self._apply_window_size(self.config.window_size_mode)

    def _on_eof(self):
        self.controls.set_playing(False)

    def _on_error(self, msg):
        self.statusBar().showMessage(f'错误: {msg}')
        QMessageBox.warning(self, '播放错误', f'发生错误:\n{msg}')

    def _screenshot(self):
        self.video.screenshot()
        self.statusBar().showMessage('截图已保存', 3000)

    def _save_playback_position(self):
        if (
            self.config.remember_playback_position
            and self._current_file
            and os.path.isfile(self._current_file)
        ):
            pos = self.video.time_pos
            if pos > 0:
                self.config.last_playback_position = pos
                self.config.last_playback_file = self._current_file

    def _show_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == SettingsDialog.Accepted:
            settings = dialog.get_settings()
            self.config.window_size_mode = settings['window_size_mode']
            self.config.default_volume = settings['default_volume']
            self.config.remember_position = settings['remember_position']
            self.config.always_on_top = settings['always_on_top']
            self.config.screenshot_dir = settings['screenshot_dir']
            self.config.remember_playback_position = settings[
                'remember_playback_position'
            ]

            self.controls.set_volume(settings['default_volume'])
            self.video._volume = settings['default_volume']
            self.on_top_action.setChecked(settings['always_on_top'])

    def _show_about(self):
        QMessageBox.about(
            self,
            '关于 FFPlayer',
            '<h2>FFPlayer</h2>'
            '<p>版本 1.7.0</p>'
            '<p>基于 ffplay (ffmpeg) 的轻量级视频播放器</p>'
            '<p>针对 ARM64 软解优化</p>'
            '<p>使用 PySide6 + ffplay 子进程构建</p>',
        )

    def _show_shortcuts(self):
        shortcuts = [
            ('空格', '播放 / 暂停'),
            ('Ctrl+O', '打开文件'),
            ('Ctrl+U', '打开网址'),
            ('Ctrl+S', '截图'),
            ('左/右方向键', '快退/快进 5秒'),
            ('Shift+左/右', '快退/快进 30秒'),
            ('上/下方向键', '音量 ±5'),
            ('] / [', '加速/减速 0.25x'),
            ('\\', '重置速度'),
            ('F', '全屏'),
            ('Esc', '退出全屏'),
            ('双击', '切换全屏'),
            ('鼠标滚轮', '调节音量'),
            ('M', '静音'),
        ]
        text = '<table cellpadding="4">'
        for key, desc in shortcuts:
            text += f'<tr><td><b>{key}</b></td><td>{desc}</td></tr>'
        text += '</table>'
        QMessageBox.information(self, '快捷键', text)

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        open_act = menu.addAction('打开文件...')
        open_act.triggered.connect(self._open_file)

        open_url_act = menu.addAction('打开网址...')
        open_url_act.triggered.connect(self._open_url)

        menu.addSeparator()

        if self._current_file:
            play_pause_act = menu.addAction(
                '暂停' if not self.video.is_paused else '播放'
            )
            play_pause_act.triggered.connect(self._toggle_play)

            stop_act = menu.addAction('停止')
            stop_act.triggered.connect(self._stop)

            menu.addSeparator()

            screenshot_act = menu.addAction('截图')
            screenshot_act.triggered.connect(self._screenshot)

        menu.addSeparator()

        fullscreen_act = menu.addAction(
            '退出全屏' if self._is_fullscreen else '全屏'
        )
        fullscreen_act.triggered.connect(self._toggle_fullscreen)

        on_top_act = menu.addAction('窗口置顶')
        on_top_act.setCheckable(True)
        on_top_act.setChecked(self.config.always_on_top)
        on_top_act.triggered.connect(self._toggle_always_on_top)

        menu.addSeparator()

        size_menu = menu.addMenu('窗口大小')
        for i, label in enumerate(SIZE_MODE_LABELS):
            act = size_menu.addAction(label)
            act.triggered.connect(
                lambda checked, idx=i: self._set_window_size_mode(idx)
            )

        menu.addSeparator()

        settings_act = menu.addAction('设置...')
        settings_act.triggered.connect(self._show_settings)

        menu.exec(event.globalPos())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            if filepath:
                self._play_file(filepath)
            else:
                url = urls[0].toString()
                if url:
                    self._play_file(url)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._toggle_fullscreen()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            new_vol = min(100, int(self.video.volume) + 5)
        else:
            new_vol = max(0, int(self.video.volume) - 5)
        self.video.volume = new_vol
        self.controls.set_volume(new_vol)
        self.config.default_volume = new_vol
        self.statusBar().showMessage(f'音量: {new_vol}%', 1500)

    def mouseMoveEvent(self, event):
        if self._is_fullscreen:
            if not self._controls_visible:
                self.controls.show()
                self._controls_visible = True
            self._fullscreen_hide_timer.start()
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Space and not modifiers:
            self._toggle_play()
        elif key == Qt.Key_Right and not modifiers:
            self.video.relative_seek(5)
        elif key == Qt.Key_Left and not modifiers:
            self.video.relative_seek(-5)
        elif key == Qt.Key_Right and modifiers & Qt.ShiftModifier:
            self.video.relative_seek(30)
        elif key == Qt.Key_Left and modifiers & Qt.ShiftModifier:
            self.video.relative_seek(-30)
        elif key == Qt.Key_Up and not modifiers:
            new_vol = min(100, int(self.video.volume) + 5)
            self.video.volume = new_vol
            self.controls.set_volume(new_vol)
        elif key == Qt.Key_Down and not modifiers:
            new_vol = max(0, int(self.video.volume) - 5)
            self.video.volume = new_vol
            self.controls.set_volume(new_vol)
        elif key == Qt.Key_F and not modifiers:
            self._toggle_fullscreen()
        elif key == Qt.Key_Escape and self._is_fullscreen:
            self._toggle_fullscreen()
        elif key == Qt.Key_BracketRight:
            self._change_speed(0.25)
        elif key == Qt.Key_BracketLeft:
            self._change_speed(-0.25)
        elif key == Qt.Key_Backslash:
            self._set_speed(1.0)
        elif key == Qt.Key_M and not modifiers:
            self._toggle_mute()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self._save_window_state()
        self._save_playback_position()
        self.config.default_volume = int(self.video.volume)
        self.video.close_player()
        super().closeEvent(event)
