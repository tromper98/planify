import logging
from typing import TypeVar

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from src.app.models.role import Role
from src.app.services import RoleService
from src.infrastructure.telegrambot.handlers.admin.keyboards.menu import get_main_menu_keyboard
from src.infrastructure.telegrambot.handlers.admin.menu.states import MenuLevel
from src.infrastructure.postgres.databaseengine import DatabaseEngine

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

Context = TypeVar('Context', bound=ContextTypes.DEFAULT_TYPE)


class MainMenuHandler:

    @staticmethod
    async def show(update: Update, context: Context, message: str = None) -> MenuLevel:
        user_id = update.effective_user.id
        user_role = RoleService(DatabaseEngine()).get_user_role_by_tg_id(user_id)

        context.user_data['current_menu'] = MenuLevel.MAIN
        context.user_data['user_role'] = user_role

        available_categories: list[dict] = MainMenuHandler._get_available_categories(user_role)

        welcome_text = MainMenuHandler._get_welcome_text(update.effective_user, user_role)

        if message:
            full_text = f'{message}\n\n{welcome_text}'
        else:
            full_text = welcome_text

        keyboard = get_main_menu_keyboard(available_categories)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=full_text,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                text=full_text,
                reply_markup=keyboard
            )

        return MenuLevel.MAIN

    @staticmethod
    def _get_available_categories(role: Role) -> list[dict]:
        base_categories = [
            {
                'id': 'meetings',
                'name': '📅 Мои встречи',
                'description': 'Просмотр и управление встречами',
                'roles': [Role.ADMIN, Role.CLIENT, Role.GUEST]
            }
        ]

        if role in [Role.ADMIN, Role.CLIENT]:
            base_categories.append({
                'id': 'slots',
                'name': '⏰ Управление слотами',
                'description': 'Создание и редактирование слотов',
                'roles': [Role.ADMIN, Role.CLIENT]
            })

        if role == Role.ADMIN:
            base_categories.append({
                'id': 'admin',
                'name': '⚙️ Администрирование',
                'description': 'Управление пользователями и системой',
                'roles': [Role.ADMIN]
            })

        # Фильтруем по роли
        return [cat for cat in base_categories if role in cat['roles']]

    @staticmethod
    def _get_welcome_text(user, role: Role) -> str:
        """Получить приветственный текст"""
        role_names = {
            Role.ADMIN: "👑 Администратор",
            Role.CLIENT: "👤 Пользователь",
            Role.GUEST: "👋 Гость"
        }

        return (
            f"Привет, {user.first_name}!\n"
            f"Ваш статус: {role_names.get(role, 'Неизвестно')}\n\n"
            "Выберите раздел:"
        )

    @staticmethod
    async def handle_selection(update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        category_id = query.data

        context.user_data['last_main_category']  = category_id

        if category_id == 'slots':
            from .slots_menu import SlotMenuHandler
            return await SlotMenuHandler.show(update, context)

        if category_id == 'appointments':
            from .appointment_menu import AppointmentMenuHandler
            return await AppointmentMenuHandler.show(update, context)

        if category_id == 'admin':
            from .admin_menu import AdminMenuHandler
            return await AdminMenuHandler.show(update, context)

        if category_id == 'settings':
            from .settings_menu import SettingsMenuHandler
            return await SettingsMenuHandler.show(update, context)

        else:
            await query.edit_message_text(
                "Раздел в разработке",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ Назад", callback_data='back_to_main')]
                ])
            )
            return MenuLevel.MAIN

    @staticmethod
    def get_handlers():
        return [
            CommandHandler('start', lambda u, c: MainMenuHandler.show(u, c)),
            CommandHandler('menu', lambda u, c: MainMenuHandler.show(u, c)),
            CallbackQueryHandler(MainMenuHandler.handle_selection, pattern='^(slots|appointments|admin|settings)$'),
            CallbackQueryHandler(lambda u, c: MainMenuHandler.show(u, c, "↩️ Возврат в главное меню"),
                                 pattern='^back_to_main$')
        ]