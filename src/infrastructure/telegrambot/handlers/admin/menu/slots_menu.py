from typing import TypeVar


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler


from src.app.models.role import Role
from src.infrastructure.telegrambot.handlers.admin.actions import AddSlotHandler
from src.infrastructure.telegrambot.handlers.admin.menu.states import MenuLevel
from src.infrastructure.telegrambot.handlers.admin.keyboards import get_slots_menu_keyboard

Context = TypeVar('Context', bound=ContextTypes.DEFAULT_TYPE)

class SlotMenuHandler:

    @staticmethod
    async def show(update: Update, context: Context, message: str = None) -> MenuLevel:
        user_id = update.effective_user.id
        user_role = context.user_data['user_role']

        context.user_data['current_menu'] = MenuLevel.SLOTS

        available_actions = SlotMenuHandler._get_available_actions(user_role)

        menu_text = "⏰ **Управление слотами**\n\nВыберите действие:"

        if message:
            menu_text = f'{message}\n\n{menu_text}'

        keyboard = get_slots_menu_keyboard(available_actions)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=menu_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )

        else:
            await update.message.reply_text(
                text=menu_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )

        return MenuLevel.SLOTS

    @staticmethod
    def _get_available_actions(role: Role) -> list[dict]:
        actions = [
            {
                'id': 'view_slots',
                'name': '👁️ Просмотреть слоты',
                'icon': '👁️',
                'roles': [Role.ADMIN, Role.CLIENT, Role.GUEST]
            },
            {
                'id': 'add_slot',
                'name': '➕ Добавить слот',
                'icon': '➕',
                'roles': [Role.ADMIN, Role.CLIENT]
            },
            {
                'id': 'edit_slot',
                'name': '✏️ Редактировать слот',
                'icon': '✏️',
                'roles': [Role.ADMIN, Role.CLIENT]
            },
            {
                'id': 'delete_slot',
                'name': '🗑️ Удалить слот',
                'icon': '🗑️',
                'roles': [Role.ADMIN]
            },
            {
                'id': 'bulk_slots',
                'name': '📅 Массовое добавление',
                'icon': '📅',
                'roles': [Role.ADMIN]
            },
            {
                'id': 'slot_statistics',
                'name': '📊 Статистика слотов',
                'icon': '📊',
                'roles': [Role.ADMIN]
            }
        ]

        # Фильтруем по роли
        return [action for action in actions if role in action['roles']]

    @staticmethod
    async def handle_selection(update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        action_id = query.data

        context.user_data['last_slots_action'] = action_id

        if action_id == 'add_slot':
            add_slot_handler = AddSlotHandler()
            return await add_slot_handler.start(update, context)

        # elif action_id == 'view_slots':
        #     view_slots_handler = ViewSlotsHandler()
        #     return await view_slots_handler.start(update, context)
        #
        # elif action_id == 'edit_slot':
        #     # Показываем меню выбора слотов для редактирования
        #     await SlotsMenuHandler._show_edit_slot_menu(update, context)
        #     return MenuLevel.SLOTS
        #
        # elif action_id == 'delete_slot':
        #     # Показываем меню выбора слотов для удаления
        #     await SlotsMenuHandler._show_delete_slot_menu(update, context)
        #     return MenuLevel.SLOTS
        #
        # elif action_id == 'bulk_slots':
        #     # Переходим к массовому добавлению
        #     from handlers.actions.bulk_slots import BulkSlotsHandler
        #     bulk_handler = BulkSlotsHandler()
        #     return await bulk_handler.start(update, context)

        else:
            await query.edit_message_text(
                "Действие не найдено",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад к слотам", callback_data='back_to_slots')]
                ])
            )
            return MenuLevel.SLOTS

    @staticmethod
    async def _show_edit_slot_menu(update: Update, context: Context):
        """Показать меню выбора слотов для редактирования"""
        from src.app.services import SlotService
        from src.infrastructure.postgres.databaseengine import DatabaseEngine

        user_id = update.effective_user.id
        slots = SlotService(DatabaseEngine()).get_slots()

        if not slots:
            keyboard = [
                [InlineKeyboardButton("➕ Создать первый слот", callback_data='add_slot')],
                [InlineKeyboardButton("↩️ Назад к слотам", callback_data='back_to_slots')]
            ]

            await update.callback_query.edit_message_text(
                text="📭 У вас нет слотов для редактирования.\n"
                     "Создайте свой первый слот!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        # Создаем клавиатуру со списком слотов
        keyboard = []
        for slot in slots[:10]:  # Ограничиваем 10 слотами для удобства
            date_str = slot['date'].strftime("%d.%m")
            time_str = slot['start_time'].strftime("%H:%M")
            button_text = f"📅 {date_str} {time_str} ({slot['duration']} мин)"
            callback_data = f"edit_slot_{slot['id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

        # Добавляем кнопки навигации
        keyboard.append([
            InlineKeyboardButton("⬅️ Пред.", callback_data='prev_page_edit'),
            InlineKeyboardButton("↩️ Назад", callback_data='back_to_slots')
        ])

        await update.callback_query.edit_message_text(
            text="✏️ **Выберите слот для редактирования:**\n\n"
                 "Отображены последние 10 слотов:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def get_handlers(self):
        """Получить обработчики меню слотов"""
        return [
            CallbackQueryHandler(self.handle_selection,
                               pattern='^(add_slot|view_slots|edit_slot|delete_slot|bulk_slots|slot_statistics)$'),
            CallbackQueryHandler(lambda u, c: self.show(u, c, "↩️ Возврат к управлению слотами"),
                               pattern='^back_to_slots$')
        ]
