from typing import TypeVar

from telegram import Update
from telegram.ext import ContextTypes

Context = TypeVar('Context', bound=ContextTypes.DEFAULT_TYPE)

class AppointmentMenuHandler:

    def show(self, update: Update, context: Context):
        ...