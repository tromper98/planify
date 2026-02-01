from enum import Enum
from datetime import datetime, date
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters

from .base import BaseHandler

class EditSlotHandler(BaseHandler):
    def __init__(self):
        super().__init__('edit_slot')