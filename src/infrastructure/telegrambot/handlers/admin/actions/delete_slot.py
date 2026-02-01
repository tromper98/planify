from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters

from src.app.models import Role
from src.app.services import RoleService, SlotService
from src.infrastructure.telegrambot.handlers.admin.keyboards.menu import get_cancel_keyboard
from src.infrastructure.postgres.databaseengine import DatabaseEngine

from .base import BaseHandler
from ..menu.navigationmanager import NavigationManager
from src.infrastructure.telegrambot.handlers.admin.menu.states import MenuLevel


class DeleteSlotStates(Enum):
    SELECT_ACTION = 1
    ENTER_SLOT_ID = 2
    CONFIRM_SINGLE_DELETE = 3
    ENTER_START_DATE = 4
    ENTER_END_DATE = 5
    CONFIRM_BULK_DELETE = 6

class DeleteSlotHandler(BaseHandler):
    def __init__(self):
        super().__init__('delete_slot')

    def define_states(self) -> type[DeleteSlotStates]:
        return DeleteSlotStates

    def is_available_for_user(self, user_id: int) -> bool:
        role_service = RoleService(DatabaseEngine())
        return role_service.get_user_role_by_tg_id(user_id) == Role.ADMIN

    def get_conversation_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start, pattern='^delete_slot$'),
                CallbackQueryHandler(self.start_with_slot_id, pattern='^delete_slot_\d+$')
            ],
            states={
                DeleteSlotStates.SELECT_ACTION: [
                    CallbackQueryHandler(self.handle_action_selection, pattern='^(delete_by_id|delete_by_period|cancel)$')
                ],
                DeleteSlotStates.ENTER_SLOT_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_slot_id_input),
                    CallbackQueryHandler(self.cancel_operation, pattern='^cancel$')
                ],
                DeleteSlotStates.CONFIRM_SINGLE_DELETE: [
                    CallbackQueryHandler(self.confirm_single_delete, pattern='^(confirm_delete|cancel)_\d+$')
                ],
                DeleteSlotStates.ENTER_START_DATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_start_date_input),
                    CallbackQueryHandler(self.cancel_operation, pattern='^cancel$')
                ],
                DeleteSlotStates.ENTER_END_DATE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_end_date_input),
                    CallbackQueryHandler(self.cancel_operation, pattern='^cancel$')
                ],
                DeleteSlotStates.CONFIRM_BULK_DELETE: [
                    CallbackQueryHandler(self.confirm_bulk_delete, pattern='^(confirm_bulk_delete|cancel)$')
                ]
            },
            fallbacks=[
                CallbackQueryHandler(self.cancel_operation, pattern='^cancel$'),
                MessageHandler(filters.Regex('^/cancel$'), self.cancel_operation),
                CallbackQueryHandler(lambda u, c: NavigationManager.go_to_menu(u, c, MenuLevel.SLOTS),
                                     pattern='^back_to_slots$'),
            ],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END
            }
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        context.user_data['delete_slot'] = {
            'user_id': update.effective_user.id,
            'return_to': MenuLevel.SLOTS
        }

        return await self.show_action_menu(update, context)

    async def start_with_slot_id(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        slot_id = int(query.data.split('_')[2])

        context.user_data['delete_slot'] = {
            'user_id': update.effective_user.id,
            'return_to': MenuLevel.SLOTS,
            'slot_id': slot_id
        }

        return await self.show_single_delete_confirmaton(update, context, slot_id)

    async def show_action_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_text = (
            "🗑️ <b>Удаление слотов</b>\n\n"
            "Выберите способ удаления:"
        )

        keyboard = [
            [
                InlineKeyboardButton("🔢 Удалить по ID", callback_data='delete_by_id'),
                InlineKeyboardButton("📅 Удалить по периоду", callback_data='delete_by_period')
            ],
            [
                InlineKeyboardButton("↩️ В меню слотов", callback_data='back_to_slots'),
                InlineKeyboardButton("❌ Отмена", callback_data='cancel')
            ]
        ]

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        return DeleteSlotStates.SELECT_ACTION

    async def handle_action_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        action = query.data

        if action == 'delete_by_id':
            await query.edit_message_text(
                text="🔢 <b>Удаление слота по ID</b>\n\n"
                     "Введите ID слота для удаления:",
                parse_mode='HTML',
                reply_markup=get_cancel_keyboard()
            )
            return DeleteSlotStates.ENTER_SLOT_ID

        elif action == 'delete_by_period':
            # Запрос даты начала периода
            await query.edit_message_text(
                text="📅 <b>Удаление слотов по периоду</b>\n\n"
                     "Введите начальную дату периода (ДД.ММ.ГГГГ):",
                parse_mode='HTML',
                reply_markup=get_cancel_keyboard()
            )
            return DeleteSlotStates.ENTER_START_DATE

        elif action == 'cancel':
            return await self.cancel_operation(update, context)

        return DeleteSlotStates.SELECT_ACTION

    async def handle_slot_id_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        slot_id_str = update.message.text.strip()

        try:
            slot_id = int(slot_id_str)
        except ValueError:
            await update.message.reply_text(
                "❌ ID слота должен быть числом.\n"
                "Попробуйте снова:",
                reply_markup=get_cancel_keyboard()
            )
            return DeleteSlotStates.ENTER_SLOT_ID

        slot_service = SlotService(DatabaseEngine())
        slot = slot_service.get_slot_by_id(slot_id)
        if not slot:
            await update.message.reply_text(
                f"❌ Слот с ID {slot_id} не найден.\n"
                "Попробуйте другой ID:",
                reply_markup=get_cancel_keyboard()
            )
            return DeleteSlotStates.ENTER_SLOT_ID

        user_id = update.effective_user.id

        if not self.is_available_for_user(user_id):
            await update.message.reply_text(
                "❌ У вас нет прав на удаление этого слота.\n"
                "Вы можете удалять только свои слоты.",
                reply_markup=get_cancel_keyboard()
            )
            return DeleteSlotStates.ENTER_SLOT_ID