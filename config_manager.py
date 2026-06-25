import json
import os
import platform
import uuid
from datetime import datetime


def _get_config_dir():
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return os.path.join(base, "MultiLLM-Chat")
    elif system == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "MultiLLM-Chat")
    else:
        return os.path.join(os.path.expanduser("~"), ".config", "MultiLLM-Chat")


def _get_screenshots_dir():
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        return os.path.join(base, "Pictures", "MultiLLM-Chat_Screenshots")
    elif system == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Pictures", "MultiLLM-Chat_Screenshots")
    else:
        return os.path.join(os.path.expanduser("~"), "Pictures", "MultiLLM-Chat_Screenshots")


PROVIDERS = ["openai", "gemini", "openrouter", "opencode"]

MODELS = {
    "OpenAI": [
        "gpt-5.5", "gpt-5.5-pro", "gpt-5.4", "gpt-5.4-mini",
        "gpt-5.3-instant", "o4", "o4-mini", "o3",
    ],
    "Gemini": [
        "gemini-3.5-flash", "gemini-3.1-flash-lite",
        "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
    ],
    "OpenRouter": [
        "openai/gpt-5.5", "openai/gpt-5.5-pro", "openai/gpt-5.4",
        "openai/gpt-5.3-instant", "openai/o4",
        "anthropic/claude-sonnet-4.6", "anthropic/claude-opus-4.8",
        "anthropic/claude-sonnet-4",
        "deepseek/deepseek-v4-pro", "deepseek/deepseek-v4-flash",
        "meta-llama/llama-4",
        "google/gemini-3.5-flash", "google/gemini-2.5-pro",
    ],
    "OpenCode": ["custom-model"],
}

MODEL_OPTIONS = [
    f"{provider} - {model}"
    for provider, models in MODELS.items()
    for model in models
]

MAX_CHATS = 50
MAX_MESSAGES_PER_CHAT = 500

DEFAULT_CONFIG = {
    "api_keys": {p: "" for p in PROVIDERS},
    "opencode_base_url": "http://localhost:11434/v1",
    "selected_model": "OpenAI - gpt-4o",
    "opacity": 1.0,
    "chat_opacity": 1.0,
    "chats": [],
    "active_chat_id": None,
}


class ConfigManager:
    def __init__(self):
        self.config_dir = _get_config_dir()
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.config = dict(DEFAULT_CONFIG)
        self._dirty = False
        self.load()

    def load(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.config.update(loaded)
        except Exception:
            pass

    def save(self, force=False):
        if not force and not self._dirty:
            return
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)
        self._dirty = False

    def _mark_dirty(self):
        self._dirty = True

    def _prune_chats(self):
        """Keep at most MAX_CHATS, remove oldest."""
        while len(self.config["chats"]) > MAX_CHATS:
            removed = self.config["chats"].pop()
            if self.config["active_chat_id"] == removed["id"]:
                self.config["active_chat_id"] = (
                    self.config["chats"][0]["id"] if self.config["chats"] else None
                )

    def _prune_messages(self, chat):
        if len(chat["messages"]) > MAX_MESSAGES_PER_CHAT:
            chat["messages"] = chat["messages"][-MAX_MESSAGES_PER_CHAT:]

    # --- API Keys ---
    def get_api_key(self, provider):
        return self.config["api_keys"].get(provider.lower(), "")

    def set_api_key(self, provider, key):
        self.config["api_keys"][provider.lower()] = key
        self._mark_dirty()
        self.save(force=True)

    # --- Model ---
    def get_selected_model(self):
        return self.config.get("selected_model", DEFAULT_CONFIG["selected_model"])

    def set_selected_model(self, model):
        self.config["selected_model"] = model
        self._mark_dirty()

    # --- Opacity ---
    def get_opacity(self):
        return float(self.config.get("opacity", 1.0))

    def set_opacity(self, value):
        self.config["opacity"] = float(value)
        self._mark_dirty()

    def get_chat_opacity(self):
        return float(self.config.get("chat_opacity", 1.0))

    def set_chat_opacity(self, value):
        self.config["chat_opacity"] = float(value)
        self._mark_dirty()

    # --- Chats ---
    def create_chat(self):
        chat_id = str(uuid.uuid4())
        chat = {
            "id": chat_id,
            "title": "New Chat",
            "messages": [],
            "created_at": datetime.now().isoformat(),
        }
        self.config["chats"].insert(0, chat)
        self.config["active_chat_id"] = chat_id
        self._prune_chats()
        self._mark_dirty()
        return chat

    def get_active_chat(self):
        for chat in self.config["chats"]:
            if chat["id"] == self.config["active_chat_id"]:
                return chat
        return None

    def set_active_chat(self, chat_id):
        self.config["active_chat_id"] = chat_id
        self._mark_dirty()

    def update_chat_title(self, chat_id, title):
        for chat in self.config["chats"]:
            if chat["id"] == chat_id:
                chat["title"] = title
                self._mark_dirty()
                break

    def delete_chat(self, chat_id):
        self.config["chats"] = [c for c in self.config["chats"] if c["id"] != chat_id]
        if self.config["active_chat_id"] == chat_id:
            self.config["active_chat_id"] = (
                self.config["chats"][0]["id"] if self.config["chats"] else None
            )
        self._mark_dirty()

    def add_message(self, chat_id, role, content):
        for chat in self.config["chats"]:
            if chat["id"] == chat_id:
                chat["messages"].append({"role": role, "content": content})
                self._prune_messages(chat)
                if role == "user" and chat["title"] == "New Chat":
                    chat["title"] = content[:50] + ("..." if len(content) > 50 else "")
                self._mark_dirty()
                break

    def get_chat_list(self):
        return [(c["id"], c["title"]) for c in self.config["chats"]]


# -- shared helpers --
def get_screenshots_dir():
    return _get_screenshots_dir()
