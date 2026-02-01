import logging

from typing import Type, TypeVar
from enum import Enum
from datetime import timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters

from .base import BaseHandler


from src.common.utils.validators import *
from src.app.models import Slot, Role
from src.app.services import SlotService, RoleService
from src.infrastructure.telegrambot.handlers.admin.keyboards.menu import get_cancel_keyboard
from src.infrastructure.postgres.databaseengine import DatabaseEngine

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

Context = TypeVar('Context', bound=ContextTypes.DEFAULT_TYPE)

class AddSlotStates(Enum):
    ENTER_DATE = 1
    ENTER_TIME = 2
    ENTER_DURATION = 3
    CHECK_TIME_INTERSECTION = 4
    CONFIRM = 5


class AddSlotHandler(BaseHandler):
    def __init__(self):
        super().__init__('add_slot')

    def define_states(self) -> Type[Enum]:
        return AddSlotStates

    def get_conversation_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start, pattern='^add_slot$')],
            states={
                AddSlotStates.ENTER_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_date_input)],
                AddSlotStates.ENTER_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_time_input)],
                AddSlotStates.ENTER_DURATION: [CallbackQueryHandler(self.handle_duration_selection, pattern='^(30|60|90|120|custom)$')],
                AddSlotStates.CHECK_TIME_INTERSECTION: [CallbackQueryHandler(self.handle_check_intersection, pattern='^(check_intersection|cancel)$')],
                AddSlotStates.CONFIRM: [CallbackQueryHandler(self.handle_confirmation, pattern='^(confirm|cancel)$')]
            },
            fallbacks=[
                CallbackQueryHandler(self.cancel, pattern='^cancel$'),
                MessageHandler(filters.Regex('^cancel$'), self.cancel)
            ],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END
            }
        )

    def is_available_for_user(self, user_id: int) -> bool:
        role_service = RoleService(DatabaseEngine())
        return role_service.get_user_role_by_tg_id(user_id) == Role.ADMIN


    async def start(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        context.user_data.clear()
        context.user_data['slot_data'] = {}

        await query.edit_message_text(
            "📅 Введите дату встречи в формате ДД.ММ.ГГГГ\n"
            "Например: 15.12.2026",
            reply_markup=get_cancel_keyboard()
        )

        return AddSlotStates.ENTER_DATE

    async def handle_date_input(self, update: Update, context: Context):
        date_str = update.message.text

        if not validate_date(date_str):
            await update.message.reply_text(
                "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ\n"
                "Попробуйте снова:",
                reply_markup=get_cancel_keyboard()
            )
            return AddSlotStates.ENTER_DATE

        slot_date = datetime.strptime(date_str, '%d.%m.%Y').date()
        context.user_data['slot_data']['date'] = slot_date

        await update.message.reply_text(
            "⏰ Введите время начала в формате ЧЧ:ММ\n"
            "Например: 14:30",
            reply_markup=get_cancel_keyboard()
        )
        return AddSlotStates.ENTER_TIME

    async def handle_time_input(self, update: Update, context: Context):
        time_str = update.message.text

        if not validate_time(time_str):
            await update.message.reply_text(
                "❌ Неверный формат времени. Используйте ЧЧ:ММ\n"
                "Попробуйте снова:",
                reply_markup=get_cancel_keyboard()
            )
            return AddSlotStates.ENTER_TIME

        start_time = datetime.strptime(time_str, '%H:%M').time()
        context.user_data['slot_data']['start_time'] = start_time

        keyboard = [
            [
                InlineKeyboardButton("30 мин", callback_data='30'),
                InlineKeyboardButton("60 мин", callback_data='60')
            ],
            [
                InlineKeyboardButton("90 мин", callback_data='90'),
                InlineKeyboardButton("120 мин", callback_data='120')
            ],
            [InlineKeyboardButton("❌ Отмена", callback_data='cancel')]
        ]

        await update.message.reply_text(
            "⏱️ Выберите продолжительность встречи:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return AddSlotStates.ENTER_DURATION

    async def handle_duration_selection(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        duration = int(query.data)
        context.user_data['slot_data']['duration'] = duration

        return await self.show_confirmation(update, context)

    async def handle_check_intersection(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        if query.data == 'check_intersection':
            slot_data = context['slot_data']
            return self._is_slot_intersect_with_other(slot_data)
        elif query.data == 'cancel':
            return await self.cancel(update, context)

        return AddSlotStates.CHECK_TIME_INTERSECTION


    async def show_confirmation(self, update: Update, context: Context):
        query = update.callback_query
        slot_data = context.user_data['slot_data']

        confirmation_text = self._format_confirmation_text(slot_data)

        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data='confirm'),
                InlineKeyboardButton("❌ Отмена", callback_data='cancel')
            ]
        ]

        await query.edit_message_text(
            text=confirmation_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return AddSlotStates.CONFIRM

    async def show_confirmation_message(self, update: Update, context: Context):
        slot_data = context.user_data['slot_data']
        confirmation_text = self._format_confirmation_text(slot_data)

        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data='confirm'),
                InlineKeyboardButton("❌ Отмена", callback_data='cancel')
            ]
        ]

        await update.message.reply_text(
            text=confirmation_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return AddSlotStates.CONFIRM

    async def handle_confirmation(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        if query.data == 'confirm':
            try:
                self._save_slot(context.user_data['slot_data'])

                await query.edit_message_text(
                    "✅ Слот успешно сохранен!\n"
                    "Для возврата в меню нажмите /start"
                )

            except Exception as e:
                logger.error(f"Ошибка сохранения слота: {e}")
                await query.edit_message_text(
                    "❌ Ошибка при сохранении. Попробуйте позже.\n"
                    "Для возврата в меню нажмите /start"
                )
        else:
            await query.edit_message_text(
                "❌ Добавление слота отменено.\n"
                "Для возврата в меню нажмите /start"
            )

        # Очищаем данные
        if 'slot_data' in context.user_data:
            del context.user_data['slot_data']

        return ConversationHandler.END

    async def cancel(self, update: Update, context: Context):
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text(
                "❌ Добавление слота отменено.\n"
                "Для возврата в меню нажмите /start"
            )

        if 'slot_data' in context.user_data:
            del context.user_data['slot_data']

        return ConversationHandler.END

    def _format_confirmation_text(self, slot_data: dict) -> str:
        date_str = slot_data['date'].strftime("%d.%m.%Y")
        time_str = slot_data['start_time'].strftime("%H:%M")
        duration = slot_data['duration']

        return (
            "📋 Проверьте введенные данные:\n\n"
            f"📅 Дата: {date_str}\n"
            f"⏰ Время начала: {time_str}\n"
            f"⏱️ Продолжительность: {duration} минут\n\n"
            "Всё верно?"
        )

    def _is_slot_intersect_with_other(self, slot_data: dict) -> bool:
        service = SlotService(DatabaseEngine())
        start_time = datetime.combine(slot_data['date'], slot_data['time'])
        end_time = start_time + timedelta(minutes=slot_data['duration'])

        slot = Slot(
            start_time=start_time,
            end_time=end_time,
            duration_in_minutes=slot_data['duration'],
        )

        return service.is_slot_intersect_with_others(slot)

    def _save_slot(self, slot_data: dict) -> None:
        service = SlotService(DatabaseEngine())
        start_time = datetime.combine(slot_data['date'], slot_data['time'])
        end_time = start_time + timedelta(minutes=slot_data['duration'])

        slot = Slot(
            start_time = start_time,
            end_time = end_time,
            duration_in_minutes = slot_data['duration'],
        )

        service.add_slot(slot)
