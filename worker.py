import queue
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from api_clients import get_client


class StreamWorker(QThread):
    token_received = pyqtSignal(str)
    stream_error = pyqtSignal(str)
    stream_finished = pyqtSignal(str)

    def __init__(self, provider, messages, api_key, model, base_url=None):
        super().__init__()
        self.provider = provider
        self.messages = messages
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._is_running = True

    def run(self):
        client = get_client(self.provider)
        if client is None:
            self.stream_error.emit(f"Unknown provider: {self.provider}")
            self.stream_finished.emit("")
            return

        q = queue.Queue()
        extra = {}
        if self.base_url:
            extra["base_url"] = self.base_url

        thread = threading.Thread(
            target=client.stream_chat,
            args=(self.messages, q, self.api_key, self.model),
            kwargs=extra,
            daemon=True,
        )
        thread.start()

        full_text = ""
        while self._is_running:
            try:
                token = q.get(timeout=0.5)
                if token is None:
                    break
                if token.startswith("\n\n[Error"):
                    self.stream_error.emit(token)
                    self.stream_finished.emit("")
                    return
                full_text += token
                self.token_received.emit(token)
            except queue.Empty:
                continue

        self.stream_finished.emit(full_text)

    def stop(self):
        self._is_running = False
