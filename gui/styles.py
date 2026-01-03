"""
Стили для темной темы интерфейса
"""
DARK_STYLE = """
QMainWindow {
    background-color: #1e1e1e;
    color: #ffffff;
}

QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

QTabWidget::pane {
    border: 1px solid #3d3d3d;
    background-color: #252525;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #cccccc;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QTabBar::tab:hover {
    background-color: #3d3d3d;
}

QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #3d3d3d;
    color: #666666;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 6px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #0078d4;
}

QComboBox {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 6px;
}

QComboBox:hover {
    border: 1px solid #0078d4;
}

QComboBox::drop-down {
    border: none;
    background-color: #2d2d2d;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    color: #ffffff;
    selection-background-color: #0078d4;
    border: 1px solid #3d3d3d;
}

QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #3d3d3d;
    min-height: 20px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4d4d4d;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2d2d2d;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #3d3d3d;
    min-width: 20px;
    border-radius: 6px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #4d4d4d;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QLabel {
    color: #ffffff;
}

QGroupBox {
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 10px;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QListWidget {
    background-color: #2d2d2d;
    color: #ffffff;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
}

QListWidget::item {
    padding: 5px;
}

QListWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #3d3d3d;
}

QProgressBar {
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    text-align: center;
    background-color: #2d2d2d;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 3px;
}

QMessageBox {
    background-color: #1e1e1e;
    color: #ffffff;
}

QMessageBox QPushButton {
    min-width: 80px;
}
"""


