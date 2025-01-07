import typing
import io
from collections.abc import Sequence, Collection
from typing import BinaryIO
from os import getenv

import requests
import json
from requests import Response

PROXIES = {
    'http': '',
    'https': '',
}

if (proxy_url := getenv("PROXY_URL")) is not None:
    PROXIES = {
        'http': proxy_url,
        'https': proxy_url,
    }

API_KEY = getenv("API_KEY")
if API_KEY is None:
    raise ValueError("API_KEY env var is None.")

# URL = "https://api.proxyapi.ru/openai/v1/chat/completions"
URL = "https://api.groq.com/openai/v1/chat/completions"
TRANSCRIPT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

Message = dict[str, str]
Messages = list[Message]
RequestData = dict[str, Sequence[Collection[str]]]

def build_request_json(context: Messages) -> RequestData:
    json = {
        # "model": "gpt-4o-mini",
        # "model": "llama3-8b-8192",
        "model": "llama-3.3-70b-versatile",
        "messages": context,
    }
    return json

def build_audio2text_json(filename: str, content) -> dict:
    files = {
        "model": (None, "whisper-large-v3-turbo"),
        "file": (filename, content),
        "response_format": (None, "text"),
    }
    return files

def update_context(context: Messages, message: str, role: str) -> Messages:
    context.append({"role": role, "content": message})
    return context

def send_text_request(user_message: str, context: Messages) -> tuple[str, Messages]:
    new_context = update_context(context, user_message, "user")
    json_data: RequestData = build_request_json(context)
    response: dict = requests.post(URL, headers=HEADERS, json=json_data, proxies=PROXIES).json()
    if 'error' in response.keys():
        if (error := response.get("error", None)) is not None and error.get("code", None) == "rate_limit_exceeded":
            return ("Я устала :(\nПодожди немного и снова сможешь написать мне. Ня~", context)
        return ("Хрен знает что случилось :/", context)
    response_content = response["choices"][0]["message"]["content"]
    new_context = update_context(context, response_content, "assistant")
    return (response_content, new_context)

def send_transcription_request(filename: str, content) -> str:
    files = build_audio2text_json(filename, content)
    response = requests.post(TRANSCRIPT_URL, headers=HEADERS, files=files, proxies=PROXIES)
    return response.text

if __name__ == "__main__":
    print("Welcome to the text version of MikuBot!")
    context: Messages = []
    while True:
        response, context = send_text_request(input(">>> "), context)
        print(response)

