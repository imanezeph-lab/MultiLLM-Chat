import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from config_manager import ConfigManager
from app import ChatWindow


APP_QSS = """
/* Global */
QMainWindow, QWidget {
    background-color: #212121;
    color: #C5C5D2;
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
}

/* Sidebar */
QFrame#sidebar {
    background-color: #171717;
    border-right: 1px solid #2F2F2F;
}

QListWidget#chatList {
    background-color: #171717;
    color: #C5C5D2;
    border: none;
    font-size: 13px;
    outline: none;
}

QListWidget#chatList::item {
    border-radius: 6px;
    padding: 6px 8px;
}

QListWidget#chatList::item:hover {
    background-color: #2A2A2A;
}

QListWidget#chatList::item:selected {
    background-color: #2F2F2F;
    color: #FFFFFF;
}

/* Chat display */
QTextBrowser#chatDisplay {
    background-color: #212121;
    color: #C5C5D2;
    border: none;
    font-size: 14px;
}

QTextBrowser#chatDisplay QScrollBar:vertical {
    background: #212121;
    width: 8px;
    margin: 0;
}

QTextBrowser#chatDisplay QScrollBar::handle:vertical {
    background: #3E3E3E;
    border-radius: 4px;
    min-height: 30px;
}

QTextBrowser#chatDisplay QScrollBar::handle:vertical:hover {
    background: #5E5E5E;
}

QTextBrowser#chatDisplay QScrollBar::add-line:vertical,
QTextBrowser#chatDisplay QScrollBar::sub-line:vertical {
    height: 0;
}

/* Input area frame */
QFrame#inputFrame {
    background-color: #2F2F2F;
    border: 1px solid #3E3E3E;
    border-radius: 12px;
    padding: 0 4px;
}

QFrame#inputFrame:focus-within {
    border: 1px solid #5E5E5E;
}

QTextEdit#inputEdit {
    background-color: transparent;
    color: #ECECF1;
    border: none;
    padding: 8px 10px;
    font-size: 14px;
    selection-background-color: #3E3E3E;
}

QTextEdit#inputEdit:focus {
    border: none;
}

QTextEdit#inputEdit::placeholder {
    color: #8E8EA0;
}

/* Image chip */
QFrame#imageChip {
    background-color: #3E3E3E;
    border-radius: 8px;
    margin: 0 8px;
}

/* Send button */
QPushButton#sendBtn {
    background-color: #FFFFFF;
    color: #212121;
    border: none;
    border-radius: 20px;
    font-size: 16px;
    font-weight: bold;
}

QPushButton#sendBtn:hover {
    background-color: #E0E0E0;
}

QPushButton#sendBtn:disabled {
    background-color: #3E3E3E;
    color: #5E5E5E;
}

/* Screenshot button */
QPushButton#screenshotBtn {
    background-color: transparent;
    color: #8E8EA0;
    border: none;
    border-radius: 20px;
    font-size: 18px;
}

QPushButton#screenshotBtn:hover {
    background-color: #2F2F2F;
    color: #ECECF1;
}

/* Combo box (model selector) */
QComboBox {
    background-color: #2F2F2F;
    color: #ECECF1;
    border: none;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    min-width: 200px;
    max-width: 300px;
}

QComboBox:hover {
    background-color: #3E3E3E;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #2F2F2F;
    color: #ECECF1;
    border: 1px solid #3E3E3E;
    selection-background-color: #3E3E3E;
    outline: none;
    padding: 4px;
}

/* Scrollbar */
QScrollBar:vertical {
    background: #212121;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #3E3E3E;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #5E5E5E;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Settings dialog */
QDialog#settingsDialog {
    background-color: #212121;
}

QLineEdit {
    background-color: #2F2F2F;
    color: #ECECF1;
    border: 1px solid #3E3E3E;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 13px;
    selection-background-color: #3E3E3E;
}

QLineEdit:focus {
    border: 1px solid #10A37F;
}

QLineEdit::placeholder {
    color: #5E5E5E;
}

QCheckBox {
    color: #8E8EA0;
    font-size: 12px;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #5E5E5E;
    background: #2F2F2F;
}

QCheckBox::indicator:checked {
    background: #10A37F;
    border-color: #10A37F;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #3E3E3E;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: none;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #E0E0E0;
}

QSlider::sub-page:horizontal {
    background: #10A37F;
    border-radius: 3px;
}

/* Scroll area in settings */
QScrollArea {
    background: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)
    app.setFont(QFont("Segoe UI", 10))

    config = ConfigManager()
    window = ChatWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
