DARK_STYLE = """
QMainWindow, QDialog {
    background-color: #1e1e2e;
}
QWidget {
    color: #cdd6f4;
    font-family: "Microsoft YaHei", "SimHei", "Segoe UI", sans-serif;
    font-size: 13px;
}
QPushButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    color: #cdd6f4;
    font-size: 13px;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.12);
}
QPushButton:pressed {
    background-color: rgba(255, 255, 255, 0.06);
}
QSlider::groove:horizontal {
    height: 3px;
    background: #45475a;
    border-radius: 1px;
}
QSlider::handle:horizontal {
    width: 12px;
    height: 12px;
    margin: -5px 0;
    background: #89b4fa;
    border-radius: 6px;
}
QSlider::handle:horizontal:hover {
    background: #b4d0fb;
    width: 14px;
    height: 14px;
    margin: -6px 0;
}
QSlider::sub-page:horizontal {
    background: #89b4fa;
    border-radius: 1px;
}
QMenuBar {
    background-color: #181825;
    color: #bac2de;
    border-bottom: 1px solid #313244;
    padding: 2px;
}
QMenuBar::item {
    padding: 4px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #313244;
}
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 28px 6px 16px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #313244;
}
QMenu::separator {
    height: 1px;
    background: #313244;
    margin: 4px 8px;
}
QStatusBar {
    background-color: #181825;
    color: #6c7086;
    border-top: 1px solid #313244;
    font-size: 12px;
}
QLabel {
    color: #cdd6f4;
    background: transparent;
}
QGroupBox {
    border: 1px solid #313244;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 18px;
    color: #cdd6f4;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QComboBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 12px;
    color: #cdd6f4;
    min-height: 24px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #1e1e2e;
    color: #cdd6f4;
    selection-background-color: #313244;
    border: 1px solid #313244;
}
QSpinBox {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    color: #cdd6f4;
    min-height: 24px;
}
QCheckBox {
    color: #cdd6f4;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #45475a;
    background-color: #313244;
}
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}
QLineEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
    color: #cdd6f4;
}
QLineEdit:focus {
    border-color: #89b4fa;
}
QDialogButtonBox QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 20px;
    color: #cdd6f4;
    min-width: 80px;
}
QDialogButtonBox QPushButton:hover {
    background-color: #45475a;
    border-color: #585b70;
}
QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 4px 8px;
}
"""
