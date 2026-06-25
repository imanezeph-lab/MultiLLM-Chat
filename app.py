import html
import os
import markdown as md_lib
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QTextBrowser, QTextEdit, QPushButton,
    QListWidget, QListWidgetItem, QComboBox, QLabel,
    QScrollBar, QApplication, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence, QTextCursor

from config_manager import ConfigManager, MODEL_OPTIONS, get_screenshots_dir
from api_clients import encode_image_to_data_url, make_image_message
from ui_components import SettingsDialog
from worker import StreamWorker


MARKDOWN_EXTENSIONS = ['fenced_code', 'codehilite', 'nl2br']


class ChatDisplay(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setObjectName("chatDisplay")
        self.messages = []
        self._streaming = False

    def clear_messages(self):
        self.messages = []
        self._streaming = False
        self._render_welcome()

    def _render_welcome(self):
        self.setHtml(self._welcome_html())

    def _welcome_html(self):
        return (
            '<html><head><style>'
            'body { background-color: #212121; color: #C5C5D2; '
            'font-family: "Segoe UI", "Helvetica Neue", sans-serif; '
            'font-size: 14px; margin: 0; padding: 20px; display: flex; '
            'align-items: center; justify-content: center; height: 100vh; }'
            '.welcome { text-align: center; }'
            '.welcome h1 { font-size: 28px; font-weight: 600; color: #C5C5D2; margin: 0; }'
            '.welcome p { font-size: 14px; color: #8E8EA0; margin-top: 8px; }'
            '</style></head><body>'
            '<div class="welcome">'
            '<h1>How can I help you today?</h1>'
            '<p>Select a model from the top and start a conversation.</p>'
            '</div>'
            '</body></html>'
        )

    def add_user_message(self, text):
        escaped = html.escape(text)
        self.messages.append(("user", escaped))
        self._full_render()

    def start_ai_message(self):
        self._streaming = True
        self._full_render()

    def append_ai_token(self, token):
        if not self._streaming:
            return
        self.setReadOnly(False)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(token)
        self.setReadOnly(True)
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())

    def finish_ai_message(self, raw_text):
        self._streaming = False
        rendered = md_lib.markdown(raw_text, extensions=MARKDOWN_EXTENSIONS)
        self.messages.append(("ai", rendered))
        self._full_render()

    def load_messages(self, messages_list):
        self.messages = []
        self._streaming = False
        for msg in messages_list:
            if msg["role"] == "user":
                content = msg["content"]
                if isinstance(content, list):
                    content = "[Image attached]"
                self.messages.append(("user", html.escape(content)))
            elif msg["role"] == "assistant":
                rendered = md_lib.markdown(msg["content"], extensions=MARKDOWN_EXTENSIONS)
                self.messages.append(("ai", rendered))
        self._full_render()

    def error_message(self, text):
        self._streaming = False
        escaped = html.escape(text)
        self.messages.append(("ai", f'<div style="color:#FF6B6B;">{escaped}</div>'))
        self._full_render()

    def _full_render(self):
        if not self.messages and not self._streaming:
            self._render_welcome()
            return

        parts = [
            '<html><head><style>',
            'body { background-color: #212121; color: #C5C5D2; '
            'font-family: "Segoe UI", "Helvetica Neue", sans-serif; '
            'font-size: 14px; margin: 0; padding: 20px 40px; }',
            'pre { background-color: #1E1E1E; padding: 12px 16px; border-radius: 8px; '
            'overflow-x: auto; margin: 8px 0; }',
            'code { background-color: #1E1E1E; padding: 2px 6px; border-radius: 4px; '
            'font-family: Consolas, "Courier New", monospace; font-size: 13px; }',
            'pre code { background: none; padding: 0; }',
            'p { margin: 6px 0; }',
            'h1, h2, h3, h4 { color: #ECECF1; }',
            'a { color: #10A37F; }',
            'blockquote { border-left: 3px solid #3E3E3E; margin: 8px 0; padding: 4px 12px; color: #8E8EA0; }',
            'ul, ol { padding-left: 24px; }',
            'table { border-collapse: collapse; margin: 8px 0; }',
            'th, td { border: 1px solid #3E3E3E; padding: 6px 12px; text-align: left; }',
            'th { background-color: #2A2A2A; }',
            '</style></head><body>',
        ]

        for role, content in self.messages:
            if role == "user":
                parts.append(
                    f'<div style="display: flex; justify-content: flex-end; '
                    f'margin: 12px 0px;">'
                    f'<div style="background-color: #2F2F2F; color: #ECECF1; '
                    f'padding: 10px 16px; border-radius: 15px; '
                    f'max-width: 70%; word-wrap: break-word; line-height: 1.5;">'
                    f'{content}</div></div>'
                )
            elif role == "ai":
                parts.append(
                    f'<div style="margin: 12px 0px; max-width: 100%; '
                    f'line-height: 1.6;">{content}</div>'
                )

        parts.append('</body></html>')
        self.setHtml(''.join(parts))
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())


class ChatInput(QWidget):
    send_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("inputWidget")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.screenshot_btn = QPushButton("\U0001F4F7")
        self.screenshot_btn.setObjectName("screenshotBtn")
        self.screenshot_btn.setFixedSize(40, 40)
        self.screenshot_btn.setToolTip("Take Screenshot")

        self.input_frame = QFrame()
        self.input_frame.setObjectName("inputFrame")
        input_layout = QVBoxLayout(self.input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(2)

        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("inputEdit")
        self.text_edit.setPlaceholderText("Message ChatGPT...")
        self.text_edit.setFixedHeight(44)
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.text_edit.textChanged.connect(self._on_text_changed)

        self.image_chip = QFrame()
        self.image_chip.setObjectName("imageChip")
        self.image_chip.setFixedHeight(0)
        self.image_chip.setVisible(False)
        chip_layout = QHBoxLayout(self.image_chip)
        chip_layout.setContentsMargins(4, 2, 4, 2)
        chip_layout.setSpacing(4)

        self.chip_thumbnail = QLabel()
        self.chip_thumbnail.setFixedSize(48, 48)
        self.chip_thumbnail.setScaledContents(True)
        chip_layout.addWidget(self.chip_thumbnail)

        self.chip_label = QLabel("Screenshot attached")
        self.chip_label.setStyleSheet("color: #8E8EA0; font-size: 12px;")
        chip_layout.addWidget(self.chip_label)
        chip_layout.addStretch()

        self.chip_remove = QPushButton("\u00d7")
        self.chip_remove.setFixedSize(20, 20)
        self.chip_remove.setStyleSheet("""
            QPushButton { background: transparent; color: #8E8EA0; border: none;
            font-size: 16px; font-weight: bold; }
            QPushButton:hover { color: #ECECF1; }
        """)
        self.chip_remove.clicked.connect(self._remove_image)
        chip_layout.addWidget(self.chip_remove)

        input_layout.addWidget(self.text_edit)
        input_layout.addWidget(self.image_chip)

        self.send_btn = QPushButton("\u2191")
        self.send_btn.setObjectName("sendBtn")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setEnabled(False)
        self.send_btn.setToolTip("Send")

        self.screenshot_btn.clicked.connect(self._on_screenshot)
        self.send_btn.clicked.connect(self.send_requested)

        layout.addWidget(self.screenshot_btn)
        layout.addWidget(self.input_frame, 1)
        layout.addWidget(self.send_btn)

        self._attached_image_path = None

    def _on_text_changed(self):
        text = self.text_edit.toPlainText().strip()
        has_content = bool(text) or self._attached_image_path is not None
        self.send_btn.setEnabled(has_content)

        doc = self.text_edit.document()
        line_count = doc.lineCount()
        doc_height = int(round(doc.size().height()))
        new_height = max(44, min(120, doc_height + 8))
        self.text_edit.setFixedHeight(new_height)

    def _on_screenshot(self):
        win = self.window()
        if win:
            win.hide()
        QTimer.singleShot(200, self._capture_screen)

    def _capture_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            pixmap = screen.grabWindow(0)
            pics_dir = get_screenshots_dir()
            os.makedirs(pics_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(pics_dir, f"MultiLLM-Chat_{ts}.png")
            pixmap.save(filepath, "PNG")
            self._attach_image(filepath)
            win = self.window()
            if win:
                win.show()

    def _attach_image(self, filepath):
        self._attached_image_path = filepath
        pixmap = QPixmap(filepath)
        self.chip_thumbnail.setPixmap(pixmap)
        self.image_chip.setFixedHeight(56)
        self.image_chip.setVisible(True)
        self.send_btn.setEnabled(True)

    def _remove_image(self):
        self._attached_image_path = None
        self.image_chip.setFixedHeight(0)
        self.image_chip.setVisible(False)
        self._on_text_changed()

    def get_text(self):
        return self.text_edit.toPlainText().strip()

    def clear(self):
        self.text_edit.clear()
        self._remove_image()

    def get_attached_image_path(self):
        return self._attached_image_path

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if self.send_btn.isEnabled():
                self.send_requested.emit()
            event.accept()
        elif event.key() == Qt.Key.Key_Return and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.text_edit.insertPlainText("\n")
            event.accept()
        else:
            super().keyPressEvent(event)


class Sidebar(QFrame):
    chat_selected = pyqtSignal(str)
    new_chat_requested = pyqtSignal()

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.cfg = config_manager
        self.setObjectName("sidebar")
        self.setFixedWidth(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)

        # Title
        title = QLabel("MultiLLM Chat")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ECECF1; padding: 0 8px 8px;")
        layout.addWidget(title)

        # New Chat button
        new_chat_btn = QPushButton("+ New Chat")
        new_chat_btn.setObjectName("newChatBtn")
        new_chat_btn.setStyleSheet("""
            QPushButton#newChatBtn {
                background-color: #2F2F2F; color: #ECECF1; border: none;
                border-radius: 8px; padding: 8px 12px; font-size: 13px;
                text-align: left;
            }
            QPushButton#newChatBtn:hover { background-color: #3E3E3E; }
        """)
        new_chat_btn.clicked.connect(self.new_chat_requested)
        layout.addWidget(new_chat_btn)

        # Chat list
        self.chat_list = QListWidget()
        self.chat_list.setObjectName("chatList")
        self.chat_list.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_list.setSpacing(2)
        self.chat_list.currentItemChanged.connect(self._on_chat_selected)
        layout.addWidget(self.chat_list, 1)

        # Bottom buttons
        bottom_frame = QFrame()
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(0, 8, 0, 0)
        bottom_layout.setSpacing(4)

        self.focus_btn = QPushButton("Focus Mode")
        self.focus_btn.setObjectName("focusBtn")
        self.focus_btn.setStyleSheet("""
            QPushButton#focusBtn {
                background-color: #2F2F2F; color: #C5C5D2; border: none;
                border-radius: 8px; padding: 8px 12px; font-size: 13px;
                text-align: left;
            }
            QPushButton#focusBtn:hover { background-color: #3E3E3E; }
        """)
        bottom_layout.addWidget(self.focus_btn)

        settings_btn = QPushButton("\u2699 Settings")
        settings_btn.setObjectName("settingsBtn")
        settings_btn.setStyleSheet("""
            QPushButton#settingsBtn {
                background-color: #2F2F2F; color: #C5C5D2; border: none;
                border-radius: 8px; padding: 8px 12px; font-size: 13px;
                text-align: left;
            }
            QPushButton#settingsBtn:hover { background-color: #3E3E3E; }
        """)
        settings_btn.clicked.connect(self._open_settings)
        bottom_layout.addWidget(settings_btn)

        layout.addWidget(bottom_frame)

        self.settings_requested = settings_btn.clicked

    def _on_chat_selected(self, current, previous):
        if current:
            cid = current.data(Qt.ItemDataRole.UserRole)
            if cid:
                self.chat_selected.emit(cid)

    def _open_settings(self):
        dlg = SettingsDialog(self.window(), self.cfg)
        dlg.exec()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            if not child or isinstance(child, QLabel):
                win = self.window()
                if isinstance(win, ChatWindow):
                    win.drag_pos = event.globalPosition().toPoint()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            win = self.window()
            if isinstance(win, ChatWindow) and win.drag_pos:
                delta = event.globalPosition().toPoint() - win.drag_pos
                win.move(win.pos() + delta)
                win.drag_pos = event.globalPosition().toPoint()
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        win = self.window()
        if isinstance(win, ChatWindow):
            win.drag_pos = None
        super().mouseReleaseEvent(event)

    def refresh(self):
        self.chat_list.blockSignals(True)
        self.chat_list.clear()
        active_id = self.cfg.config.get("active_chat_id")
        for cid, title in self.cfg.get_chat_list():
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, cid)
            if cid == active_id:
                item.setSelected(True)
            self.chat_list.addItem(item)
        self.chat_list.blockSignals(False)


class ChatWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.cfg = config_manager
        self.focus_mode = False
        self._normal_geometry = None
        self.drag_pos = None
        self.stream_worker = None

        self.setWindowTitle("MultiLLM Chat")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self.cfg, self)
        self.sidebar.chat_selected.connect(self.load_chat)
        self.sidebar.new_chat_requested.connect(self.new_chat)
        self.sidebar.focus_btn.clicked.connect(self.toggle_focus_mode)
        main_layout.addWidget(self.sidebar)

        # Chat area
        chat_area = QFrame()
        chat_area.setObjectName("chatArea")
        chat_area.setStyleSheet("QFrame#chatArea { background-color: #212121; }")
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)

        # Drag handle for window moving (visible in both modes)
        self.drag_handle = QFrame()
        self.drag_handle.setObjectName("dragHandle")
        self.drag_handle.setFixedHeight(8)
        self.drag_handle.setCursor(Qt.CursorShape.OpenHandCursor)
        self.drag_handle.setMouseTracking(True)
        self.drag_handle.installEventFilter(self)
        chat_layout.addWidget(self.drag_handle)

        # Model selector at top center
        self.model_bar = QFrame()
        self.model_bar.setObjectName("modelBar")
        self.model_bar.setFixedHeight(52)
        self.model_bar.setStyleSheet("QFrame#modelBar { background-color: #212121; border-bottom: 1px solid #2F2F2F; }")
        model_bar_layout = QHBoxLayout(self.model_bar)
        model_bar_layout.setContentsMargins(0, 0, 0, 0)

        self.model_combo = QComboBox()
        self.model_combo.setObjectName("modelCombo")
        self.model_combo.addItems(MODEL_OPTIONS)
        selected = self.cfg.get_selected_model()
        idx = self.model_combo.findText(selected)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        self.model_combo.setStyleSheet("""
            QComboBox#modelCombo {
                background-color: #2F2F2F; color: #ECECF1; border: none;
                border-radius: 8px; padding: 6px 12px; font-size: 13px;
                min-width: 200px; max-width: 300px;
            }
            QComboBox#modelCombo:hover { background-color: #3E3E3E; }
            QComboBox#modelCombo::drop-down { border: none; padding-right: 8px; }
            QComboBox#modelCombo QAbstractItemView {
                background-color: #2F2F2F; color: #ECECF1; border: 1px solid #3E3E3E;
                selection-background-color: #3E3E3E; outline: none;
            }
        """)
        self.model_combo.currentTextChanged.connect(self._on_model_change)
        model_bar_layout.addStretch()
        model_bar_layout.addWidget(self.model_combo)
        model_bar_layout.addStretch()
        self.model_bar.installEventFilter(self)
        chat_layout.addWidget(self.model_bar)

        # Chat display
        self.chat_display = ChatDisplay()
        chat_layout.addWidget(self.chat_display, 1)

        # Input area
        input_container = QFrame()
        input_container.setObjectName("inputContainer")
        input_container.setStyleSheet("QFrame#inputContainer { background-color: #212121; padding: 8px 40px 16px; }")
        input_container_layout = QVBoxLayout(input_container)
        input_container_layout.setContentsMargins(0, 0, 0, 0)

        self.chat_input = ChatInput()
        self.chat_input.send_requested.connect(self.send_message)
        input_container_layout.addWidget(self.chat_input)
        chat_layout.addWidget(input_container)

        main_layout.addWidget(chat_area, 1)

        # Focus mode shortcut
        QShortcut(QKeySequence("Ctrl+Shift+F"), self).activated.connect(self.toggle_focus_mode)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._on_escape)

        # Opacity effects
        self.chat_opacity_effect = None
        self.input_opacity_effect = None
        self.apply_opacities()

        # State
        self.stream_buffer = ""
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.timeout.connect(lambda: self.cfg.save())
        self._auto_save_timer.start(30000)

        # Load last chat
        self.sidebar.refresh()
        chat = self.cfg.get_active_chat()
        if chat and chat["messages"]:
            self.chat_display.load_messages(chat["messages"])
        else:
            self.chat_display._render_welcome()

    def apply_opacities(self):
        win_opacity = self.cfg.get_opacity()
        self.setWindowOpacity(win_opacity)

        chat_opacity = self.cfg.get_chat_opacity()
        if chat_opacity < 1.0:
            if self.chat_opacity_effect is None:
                self.chat_opacity_effect = QGraphicsOpacityEffect(self)
                self.input_opacity_effect = QGraphicsOpacityEffect(self)
            self.chat_opacity_effect.setOpacity(chat_opacity)
            self.input_opacity_effect.setOpacity(chat_opacity)
            self.chat_display.setGraphicsEffect(self.chat_opacity_effect)
            self.chat_input.setGraphicsEffect(self.input_opacity_effect)
        else:
            self.chat_display.setGraphicsEffect(None)
            self.chat_input.setGraphicsEffect(None)
            self.chat_opacity_effect = None
            self.input_opacity_effect = None

    def _is_over_widget(self, obj, event, widget):
        """Check if an event is over a specific child widget."""
        pos = event.position().toPoint()
        child = obj.childAt(pos)
        while child:
            if child is widget:
                return True
            child = child.parent()
        return False

    def _try_drag(self, obj, event):
        pos = event.position().toPoint()
        child = obj.childAt(pos)
        # Don't drag if clicking on an interactive widget
        if child and not isinstance(child, QFrame):
            return False
        self.drag_pos = event.globalPosition().toPoint()
        return True

    def eventFilter(self, obj, event):
        if obj is self.drag_handle:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.drag_pos = event.globalPosition().toPoint()
                    return True
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() & Qt.MouseButton.LeftButton and self.drag_pos:
                    delta = event.globalPosition().toPoint() - self.drag_pos
                    self.move(self.pos() + delta)
                    self.drag_pos = event.globalPosition().toPoint()
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.drag_pos = None
                return True
        elif obj is self.model_bar:
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    if self._try_drag(obj, event):
                        return True
            elif event.type() == QEvent.Type.MouseMove:
                if event.buttons() & Qt.MouseButton.LeftButton and self.drag_pos:
                    delta = event.globalPosition().toPoint() - self.drag_pos
                    self.move(self.pos() + delta)
                    self.drag_pos = event.globalPosition().toPoint()
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.drag_pos = None
                return True
        return super().eventFilter(obj, event)

    def toggle_focus_mode(self):
        self.focus_mode = not self.focus_mode
        if self.focus_mode:
            self._normal_geometry = self.geometry()
            self.sidebar.hide()
            self.model_bar.hide()
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
            self.show()
            self.resize(520, 380)
            self.sidebar.focus_btn.setText("Exit Focus")
        else:
            self.sidebar.show()
            self.model_bar.show()
            self.setWindowFlags(Qt.WindowType.Window)
            self.show()
            if self._normal_geometry:
                self.setGeometry(self._normal_geometry)
            self.sidebar.focus_btn.setText("Focus Mode")

    def _on_escape(self):
        if self.focus_mode:
            self.toggle_focus_mode()

    def new_chat(self):
        if self.stream_worker and self.stream_worker.isRunning():
            return
        self.cfg.create_chat()
        self.chat_display.clear_messages()
        self.sidebar.refresh()

    def load_chat(self, chat_id):
        if self.stream_worker and self.stream_worker.isRunning():
            return
        self.cfg.set_active_chat(chat_id)
        chat = self.cfg.get_active_chat()
        if chat and chat["messages"]:
            self.chat_display.load_messages(chat["messages"])
        else:
            self.chat_display.clear_messages()
        self.sidebar.refresh()

    def send_message(self):
        if self.stream_worker and self.stream_worker.isRunning():
            return

        text = self.chat_input.get_text()
        image_path = self.chat_input.get_attached_image_path()

        if not text and not image_path:
            return

        self.chat_input.setEnabled(False)

        # Ensure chat exists
        chat = self.cfg.get_active_chat()
        if not chat:
            self.cfg.create_chat()
            chat = self.cfg.get_active_chat()
            self.sidebar.refresh()

        # Build message content
        if image_path and text:
            data_url = encode_image_to_data_url(image_path)
            content = make_image_message(text, data_url)
        elif image_path:
            data_url = encode_image_to_data_url(image_path)
            content = make_image_message("", data_url)
        else:
            content = text

        # Display user message
        display_text = text if text else "[Image attached]"
        self.chat_display.add_user_message(display_text)

        # Save to history
        self.cfg.add_message(chat["id"], "user", content)
        self.sidebar.refresh()

        self.chat_input.clear()

        # Determine provider & model
        model_display = self.model_combo.currentText()
        if " - " not in model_display:
            self._display_error("No model selected.")
            self.chat_input.setEnabled(True)
            return

        provider_name, model_name = model_display.split(" - ", 1)
        provider_key = provider_name.lower()
        api_key = self.cfg.get_api_key(provider_key)
        if not api_key:
            self._display_error(f"{provider_name} API key not configured. Open Settings.")
            self.chat_input.setEnabled(True)
            return

        # Prepare messages
        messages = self._prepare_api_messages(chat)

        # Start streaming
        extra = {}
        if provider_key == "opencode":
            extra["base_url"] = self.cfg.config.get("opencode_base_url", "http://localhost:11434/v1")

        self.stream_buffer = ""
        self.chat_display.start_ai_message()

        self.stream_worker = StreamWorker(
            provider_key, messages, api_key, model_name, **extra
        )
        self.stream_worker.token_received.connect(self._on_token)
        self.stream_worker.stream_error.connect(self._on_stream_error)
        self.stream_worker.stream_finished.connect(self._on_stream_finished)
        self.stream_worker.finished.connect(self._on_worker_finished)
        self.stream_worker.start()

    def _prepare_api_messages(self, chat):
        messages = []
        for msg in chat["messages"]:
            content = msg["content"]
            if isinstance(content, list):
                messages.append({"role": msg["role"], "content": content})
            elif isinstance(content, str):
                try:
                    text = content
                    messages.append({"role": msg["role"], "content": text})
                except Exception:
                    messages.append({"role": msg["role"], "content": str(content)})
            else:
                messages.append({"role": msg["role"], "content": str(content)})
        return messages

    def _on_token(self, token):
        self.stream_buffer += token
        self.chat_display.append_ai_token(token)

    def _on_stream_error(self, error_text):
        self.chat_display.error_message(error_text)

    def _on_stream_finished(self, full_text):
        if full_text:
            self.chat_display.finish_ai_message(full_text)
            chat = self.cfg.get_active_chat()
            if chat:
                self.cfg.add_message(chat["id"], "assistant", full_text)

    def _on_worker_finished(self):
        self.chat_input.setEnabled(True)
        self.stream_worker = None

    def _display_error(self, text):
        self.chat_display.error_message(text)

    def _on_model_change(self, choice):
        self.cfg.set_selected_model(choice)

    def closeEvent(self, event):
        if self.stream_worker and self.stream_worker.isRunning():
            self.stream_worker.stop()
            self.stream_worker.wait(2000)
        self.cfg.save(force=True)
        event.accept()
