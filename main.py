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

type UserID = int
ai_contexts: dict[UserID, ai.AiContext] = {}

async def ai_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message is None or update.effective_message.text is None or update.effective_message.from_user is None:
        return

    global ai_contexts
    id: int = update.effective_message.from_user.id
    ai_context = ai_contexts.setdefault(id, ai.DefaultAiContext())
    response = ai_context.send_text(update.effective_message.text)
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=response)

async def ai_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.voice is None or update.message.voice.mime_type is None or update.message.from_user is None:
        return

    voice = update.message.voice
    mime_type = update.message.voice.mime_type
    file: telegram.File = await voice.get_file()
    audio_content = await file.download_as_bytearray()

    global ai_contexts
    id: int = update.message.from_user.id
    ai_context = ai_contexts.setdefault(id, ai.DefaultAiContext())
    (response, transcription) = ai_context.send_voice(audio_content)
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=f'Ваше сообщение распознано как: "{transcription}"')
    await context.bot.send_message(chat_id=cast(Chat, update.effective_chat).id, text=response)

async def is_bot_mentioned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.message is not None and update.message.text and context.bot.name in [update.message.text[mention.offset:mention.offset + mention.length] for mention in update.message.entities if mention['type'] == 'mention']:
        return True
    return False

async def is_reply_to_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if (message := update.message) and (reply := message.reply_to_message) and (user := reply.from_user) and user.id == cast(Bot, context.bot).id:
        return True
    return False

async def ai_text_with_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_reply_to_bot(update, context) or await is_bot_mentioned(update, context):
        await ai_text_message(update, context)

async def ai_voice_with_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_reply_to_bot(update, context) or await is_bot_mentioned(update, context):
        await ai_voice_message(update, context)

def run_bot(admin_ids: list[int]) -> None:
    BOT_TOKEN = getenv("BOT_TOKEN")
    if BOT_TOKEN is None:
        raise ValueError("BOT_TOKEN env var is None.")

    request = telegram.request.HTTPXRequest()

    application = ApplicationBuilder()\
        .request(request)\
        .get_updates_request(request)\
        .token(BOT_TOKEN)\
        .build()

    private_text_handler = MessageHandler(filters.TEXT & filters.Chat(admin_ids), ai_text_message)
    application.add_handler(private_text_handler)

    private_voice_handler = MessageHandler(filters.VOICE & filters.Chat(admin_ids), ai_voice_message)
    application.add_handler(private_voice_handler)
    
    group_text_handler = MessageHandler(filters.TEXT & filters.ChatType.GROUPS, ai_text_with_filters)
    application.add_handler(group_text_handler)

    group_voice_handler = MessageHandler(filters.VOICE & filters.ChatType.GROUPS, ai_voice_with_filters)
    application.add_handler(group_voice_handler)
    
    application.run_polling()

if __name__ == '__main__':
    print("Добро пожаловать в систему MikuSystem!")
    print("Пожалуйста, перечислите ID администраторов через запятую.")
    print('Примеры: "12462, 210582, 23366" или "1235,22,771"')
    admin_ids: list[int] = list(map(int, input(": ").replace(" ", "").split(",")))
    print("Запуск бота...")
    run_bot(admin_ids)

# TODO: переключение между модельками прямо в чате Telegram
# TODO: новая моделька в ProxyAPI - Claude
# TODO: первоначальная настройка бота и сохранение настроек в файл settings.json
# TODO: сохранение контекста после отключения бота
# TODO: умное сжатие контекста для долгосрочной памяти
# TODO: распознавание изображений через Groq
# TODO: инструктаж бота через системные промпты для улучшения ответов и придания личности Хацунэ Мику.
# TODO: озвучивание исходящих сообщений и отправка через Telegram голосом Хацуне Мику
# TODO: голосовые звонки (???)
# TODO: асинхронные запросы к моделькам
