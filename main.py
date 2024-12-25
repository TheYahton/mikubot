import requests
from os import getenv

API_KEY = getenv("BOT_API")

URL = "https://api.proxyapi.ru/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

def gen_data(message: str) -> dict:
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ]
    }
    return data

# user_input = input()
# data = gen_data(user_input)
# response = requests.post(URL, headers=HEADERS, json=data).json()
# message = response["choices"][0]["message"]["content"]

if __name__ == "__main__":
    if API_KEY is None:
        raise ValueError("API_KEY is None! Do you have `$API_KEY` environment variable?")
