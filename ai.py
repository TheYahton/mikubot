from collections.abc import Sequence, Collection
from dataclasses import dataclass, field
from enum import Enum, auto
from os import getenv

import requests
import json
from requests import Response


class ApiKind(Enum):
    ProxyAPI = auto()
    Groq = auto()

APIs: dict[ApiKind, str] = {
    ApiKind.ProxyAPI: "https://api.proxyapi.ru/openai/v1/chat/completions",
    ApiKind.Groq: "https://api.groq.com/openai/v1/chat/completions",
}

def get_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}"}

type Message = dict[str, str]
type Messages = list[Message]
type RequestData = dict[str, Sequence[Collection[str]]]

@dataclass
class AiContext:
    api: ApiKind
    api_key: str
    messages: Messages

    def send_text(self, text: str) -> str:
        (response, self.messages) = send_text_request(text, self.messages, self.api, self.api_key)
        return response

    def send_voice(self, content) -> tuple[str, str]:
        transcription = send_transcription_request("example.ogg", content, self.api_key)
        response = self.send_text(transcription)
        return (response, transcription)

@dataclass
class DefaultAiContext(AiContext):
    api: ApiKind = ApiKind.Groq
    api_key: str = getenv("API_KEY")
    messages: Messages = field(default_factory=list)

def build_request_json(messages: Messages, model: str = "llama-3.3-70b-versatile") -> RequestData:
    json = {
        # "model": "gpt-4o-mini",
        # "model": "llama3-8b-8192",
        # "model": "llama-3.3-70b-versatile",
        "model": model,
        "messages": messages,
    }
    return json

def build_audio2text_json(filename: str, content) -> dict:
    files = {
        "model": (None, "whisper-large-v3-turbo"),
        "file": (filename, content),
        "response_format": (None, "text"),
    }
    return files

def update_messages(messages: Messages, new_message: str, role: str) -> Messages:
    messages.append({"role": role, "content": new_message})
    return messages

def send_text_request(user_message: str, messages: Messages, api: ApiKind, api_key: str) -> tuple[str, Messages]:
    new_messages = update_messages(messages, user_message, "user")
    json_data: RequestData = build_request_json(messages)
    try:
        response: dict = requests.post(APIs[api], headers=get_headers(api_key), json=json_data).json()
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return "Request failed, please try again later.", messages
    if "error" in response.keys():
        if response["error"].get("code", None) == "rate_limit_exceeded":
            return ("Я устала :(\nПодожди немного и снова сможешь написать мне. Ня~", messages)
        return ("Хрен знает что случилось :/", messages)
    response_content = response["choices"][0]["message"]["content"]
    new_messages = update_messages(messages, response_content, "assistant")
    return (response_content, new_messages)

def send_transcription_request(filename: str, content, api_key: str) -> str:
    TRANSCRIPT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

    files = build_audio2text_json(filename, content)
    response = requests.post(TRANSCRIPT_URL, headers=get_headers(api_key), files=files)
    return response.text

if __name__ == "__main__":
    API_KEY = getenv("API_KEY")
    if API_KEY is None:
        raise ValueError("API_KEY env var is None.")
    print("Welcome to the text version of MikuBot!")
    messages: Messages = []
    while True:
        response, messages = send_text_request(input(">>> "), messages, ApiKind.Groq, API_KEY)
        print(response)

