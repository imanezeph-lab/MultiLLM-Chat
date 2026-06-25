import base64
import json
import requests


def _normalize_messages(messages):
    """Convert simple string-content messages to proper format.
    Handles both plain text and image content."""
    normalized = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            normalized.append({"role": msg["role"], "content": content})
        elif isinstance(content, list):
            normalized.append({"role": msg["role"], "content": content})
        else:
            normalized.append({"role": msg["role"], "content": str(content)})
    return normalized


def _sse_parse(response, queue):
    for line in response.iter_lines():
        if line:
            line = line.decode("utf-8", errors="replace").strip()
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    content = data["choices"][0]["delta"].get("content", "")
                    if content:
                        queue.put(content)
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass
    queue.put(None)


class OpenAIClient:
    def stream_chat(self, messages, queue, api_key, model="gpt-4o"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            msgs = _normalize_messages(messages)
            stream = client.chat.completions.create(
                model=model,
                messages=msgs,
                stream=True,
                timeout=60,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    queue.put(chunk.choices[0].delta.content)
            queue.put(None)
        except Exception as e:
            queue.put(f"\n\n[Error: {e}]")
            queue.put(None)


class GeminiClient:
    def stream_chat(self, messages, queue, api_key, model="gemini-2.0-flash"):
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            parts = []
            for msg in _normalize_messages(messages):
                content = msg["content"]
                if isinstance(content, list):
                    for part in content:
                        if part["type"] == "text":
                            parts.append(f"{msg['role']}: {part['text']}\n")
                        elif part["type"] == "image_url":
                            parts.append("[Image attached]\n")
                else:
                    parts.append(f"{msg['role']}: {content}\n")
            full_text = "".join(parts).strip() or "Hello"
            response = client.models.generate_content_stream(
                model=model, contents=full_text,
            )
            for chunk in response:
                if chunk.text:
                    queue.put(chunk.text)
            queue.put(None)
        except Exception as e:
            queue.put(f"\n\n[Error: {e}]")
            queue.put(None)


class OpenRouterClient:
    def stream_chat(self, messages, queue, api_key, model="openai/gpt-4o"):
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://multillm-chat.app",
                "X-Title": "MultiLLM Chat",
            }
            data = {"model": model, "messages": _normalize_messages(messages), "stream": True}
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=data, stream=True, timeout=60,
            )
            resp.raise_for_status()
            _sse_parse(resp, queue)
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                detail = resp.json().get("error", {}).get("message", str(e))
            except Exception:
                detail = str(e)
            queue.put(f"\n\n[HTTP {resp.status_code}: {detail}]")
            queue.put(None)
        except Exception as e:
            queue.put(f"\n\n[Error: {e}]")
            queue.put(None)


class OpenCodeClient:
    def stream_chat(self, messages, queue, api_key, model="default", base_url="http://localhost:11434/v1"):
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            data = {"model": model, "messages": _normalize_messages(messages), "stream": True}
            url = base_url.rstrip("/") + "/chat/completions"
            resp = requests.post(
                url, headers=headers, json=data, stream=True, timeout=60,
            )
            resp.raise_for_status()
            _sse_parse(resp, queue)
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                detail = resp.json().get("error", {}).get("message", str(e))
            except Exception:
                detail = str(e)
            queue.put(f"\n\n[HTTP {resp.status_code}: {detail}]")
            queue.put(None)
        except Exception as e:
            queue.put(f"\n\n[Error: {e}]")
            queue.put(None)


CLIENTS = {
    "openai": OpenAIClient(),
    "gemini": GeminiClient(),
    "openrouter": OpenRouterClient(),
    "opencode": OpenCodeClient(),
}


def get_client(provider):
    return CLIENTS.get(provider.lower())


def encode_image_to_data_url(image_path):
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{data}"


def make_image_message(text, image_data_url):
    parts = []
    if text:
        parts.append({"type": "text", "text": text})
    parts.append({"type": "image_url", "image_url": {"url": image_data_url}})
    return parts
