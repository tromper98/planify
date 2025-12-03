import logging

from telegram import Update
from telegram.ext import  ContextTypes


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPES):
    message = '''
        Привет! Я бот для бронирования встреч. Для того, чтобы запланировать встречу нажми 'Забронировать встречу'.
    '''
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
