import base64
import io
import os
from os import getenv
from typing import cast

import logging
import telegram
from telegram import Bot, Chat, MessageEntity, Message, Update
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler

import ai

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ai_context: ai.Messages = []

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ai_context
    response, ai_context = ai.send_text_request(cast(str, cast(Message, update.effective_message).text), ai_context)
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=response)

async def voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.voice is None or update.message.voice.mime_type is None:
        return

    voice = update.message.voice
    mime_type = update.message.voice.mime_type
    file: telegram.File = await voice.get_file()
    audio_content = await file.download_as_bytearray()
    transcription = ai.send_transcription_request("example.ogg", audio_content)

    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=f'Ваше сообщение распознано как: "{transcription}"')

    global ai_context
    response, ai_context = ai.send_text_request(transcription, ai_context)
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=response)

def run_bot(admin_ids: list[int]) -> None:
    BOT_TOKEN = getenv("BOT_TOKEN")
    if BOT_TOKEN is None:
        raise ValueError("BOT_TOKEN env var is None.")

    request = telegram.request.HTTPXRequest(proxy=getenv("PROXY_URL"))

    application = ApplicationBuilder()\
        .request(request)\
        .get_updates_request(request)\
        .token(BOT_TOKEN)\
        .build()

    private_message_handler = MessageHandler(filters.TEXT & filters.Chat(admin_ids), ai_chat)
    application.add_handler(private_message_handler)

    group_message_handler = MessageHandler(filters.TEXT & filters.ChatType.GROUPS, ai_chat)
    application.add_handler(group_message_handler)

    group_voice_handler = MessageHandler(filters.VOICE & filters.ChatType.GROUPS, voice_message)
    application.add_handler(group_voice_handler)
    
    application.run_polling()

if __name__ == '__main__':
    print("Добро пожаловать в систему MikuSystem!")
    print("Пожалуйста, перечислите ID администраторов через запятую.")
    print('Примеры: "12462, 210582, 23366" или "1235,22,771"')
    admin_ids: list[int] = list(map(int, input(": ").replace(" ", "").split(",")))
    print("Запуск бота...")
    run_bot(admin_ids)

# TODO: отдельный контекст для каждого пользователя
# TODO: переключение между модельками прямо в чате Telegram
# TODO: новая моделька в ProxyAPI - Claude
# TODO: первоначальная настройка бота и сохранение настроек в файл settings.json
# TODO: сохранение контекста после отключения бота
# TODO: умное сжатие контекста для долгосрочной памяти
# TODO: распознавание изображений через Groq
# TODO: инструктаж бота через системные промпты для улучшения ответов и придания личности Хацунэ Мику.
# TODO: озвучивание исходящих сообщений и отправка через Telegram голосом Хацуне Мику
# TODO: голосовые звонки (???)
