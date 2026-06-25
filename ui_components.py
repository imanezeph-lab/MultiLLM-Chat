from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSlider, QCheckBox, QScrollArea, QWidget, QFrame,
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.cfg = config_manager
        self.setWindowTitle("Settings")
        self.setFixedSize(520, 600)
        self.setObjectName("settingsDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px 20px 0;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(content)
        scroll_layout.setContentsMargins(20, 10, 20, 10)
        scroll_layout.setSpacing(8)

        self.entries = {}

        apis = [
            ("openai", "OpenAI API Key", "sk-..."),
            ("gemini", "Google Gemini API Key", "AIza..."),
            ("openrouter", "OpenRouter API Key", "sk-or-..."),
            ("opencode", "OpenCode / Custom Key", "(optional)"),
        ]

        for key, label, ph in apis:
            frame = QFrame()
            frame.setObjectName("settingsGroup")
            frame.setStyleSheet("""
                QFrame#settingsGroup {
                    background: #2A2A2A; border-radius: 8px; padding: 8px;
                }
            """)
            f_layout = QVBoxLayout(frame)
            f_layout.setContentsMargins(12, 8, 12, 8)
            f_layout.setSpacing(4)

            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #C5C5D2;")
            f_layout.addWidget(lbl)

            entry = QLineEdit()
            entry.setPlaceholderText(ph)
            entry.setText(self.cfg.get_api_key(key))
            entry.setEchoMode(QLineEdit.EchoMode.Password)
            f_layout.addWidget(entry)

            cb_row = QHBoxLayout()
            cb = QCheckBox("Show")
            cb.setStyleSheet("color: #8E8EA0; font-size: 12px;")
            cb.toggled.connect(
                lambda checked, e=entry: e.setEchoMode(
                    QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
                )
            )
            cb_row.addWidget(cb)
            cb_row.addStretch()
            f_layout.addLayout(cb_row)

            scroll_layout.addWidget(frame)
            self.entries[key] = entry

        # OpenCode URL
        url_frame = QFrame()
        url_frame.setObjectName("settingsGroup")
        url_frame.setStyleSheet("""
            QFrame#settingsGroup {
                background: #2A2A2A; border-radius: 8px; padding: 8px;
            }
        """)
        url_layout = QVBoxLayout(url_frame)
        url_layout.setContentsMargins(12, 8, 12, 8)
        url_layout.setSpacing(4)
        url_lbl = QLabel("OpenCode Base URL")
        url_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #C5C5D2;")
        url_layout.addWidget(url_lbl)
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("http://localhost:11434/v1")
        self.url_entry.setText(self.cfg.config.get("opencode_base_url", "http://localhost:11434/v1"))
        url_layout.addWidget(self.url_entry)
        scroll_layout.addWidget(url_frame)

        # Opacity sliders
        scroll_layout.addSpacing(10)

        # Window opacity
        win_frame = QFrame()
        win_frame.setObjectName("settingsGroup")
        win_frame.setStyleSheet("""
            QFrame#settingsGroup {
                background: #2A2A2A; border-radius: 8px; padding: 8px;
            }
        """)
        win_layout = QVBoxLayout(win_frame)
        win_layout.setContentsMargins(12, 8, 12, 8)
        win_layout.setSpacing(4)
        win_lbl = QLabel("Window Opacity")
        win_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #C5C5D2;")
        win_layout.addWidget(win_lbl)

        win_slider_row = QHBoxLayout()
        self.win_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.win_opacity_slider.setRange(30, 100)
        self.win_opacity_slider.setValue(int(self.cfg.get_opacity() * 100))
        self.win_opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.win_opacity_slider.setTickInterval(10)
        win_slider_row.addWidget(self.win_opacity_slider)

        self.win_op_label = QLabel(f"{self.win_opacity_slider.value()}%")
        self.win_op_label.setStyleSheet("color: #C5C5D2; font-size: 12px; min-width: 40px;")
        win_slider_row.addWidget(self.win_op_label)
        win_layout.addLayout(win_slider_row)
        scroll_layout.addWidget(win_frame)

        # Chat area opacity
        chat_frame = QFrame()
        chat_frame.setObjectName("settingsGroup")
        chat_frame.setStyleSheet("""
            QFrame#settingsGroup {
                background: #2A2A2A; border-radius: 8px; padding: 8px;
            }
        """)
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(12, 8, 12, 8)
        chat_layout.setSpacing(4)
        chat_lbl = QLabel("Chat Area Opacity")
        chat_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #C5C5D2;")
        chat_layout.addWidget(chat_lbl)

        chat_slider_row = QHBoxLayout()
        self.chat_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.chat_opacity_slider.setRange(30, 100)
        self.chat_opacity_slider.setValue(int(self.cfg.get_chat_opacity() * 100))
        self.chat_opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.chat_opacity_slider.setTickInterval(10)
        chat_slider_row.addWidget(self.chat_opacity_slider)

        self.chat_op_label = QLabel(f"{self.chat_opacity_slider.value()}%")
        self.chat_op_label.setStyleSheet("color: #C5C5D2; font-size: 12px; min-width: 40px;")
        chat_slider_row.addWidget(self.chat_op_label)
        chat_layout.addLayout(chat_slider_row)
        scroll_layout.addWidget(chat_frame)

        self.win_opacity_slider.valueChanged.connect(
            lambda v: self.win_op_label.setText(f"{v}%"))
        self.chat_opacity_slider.valueChanged.connect(
            lambda v: self.chat_op_label.setText(f"{v}%"))

        scroll_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("saveBtn")
        save_btn.setStyleSheet("""
            QPushButton#saveBtn {
                background-color: #10A37F; color: white; border: none;
                border-radius: 8px; padding: 10px 20px;
                font-size: 14px; font-weight: bold;
                margin: 0 20px 20px;
            }
            QPushButton#saveBtn:hover { background-color: #0E8C6E; }
        """)
        save_btn.clicked.connect(self.save)
        layout.addWidget(save_btn)

    def save(self):
        for key, entry in self.entries.items():
            self.cfg.set_api_key(key, entry.text())

        self.cfg.config["opencode_base_url"] = self.url_entry.text()
        self.cfg.set_opacity(self.win_opacity_slider.value() / 100.0)
        self.cfg.set_chat_opacity(self.chat_opacity_slider.value() / 100.0)
        self.cfg.save()

        parent = self.parent()
        if hasattr(parent, 'apply_opacities'):
            parent.apply_opacities()

        self.accept()
