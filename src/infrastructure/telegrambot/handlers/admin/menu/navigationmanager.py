from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.infrastructure.telegrambot.handlers.admin.menu.states import MenuLevel, NavigationState


class NavigationManager:

    @staticmethod
    async def go_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, target_menu: MenuLevel, message: str = None):

        if target_menu == MenuLevel.MAIN:
            from .main_menu import MainMenuHandler
            return await MainMenuHandler.show(update, context, message)

        elif target_menu == MenuLevel.SLOTS:
            from .slots_menu import SlotMenuHandler
            return await SlotMenuHandler.show(update, context, message)

        elif target_menu == MenuLevel.APPOINTMENTS:
            from .appointment_menu import AppointmentMenuHandler
            return await AppointmentMenuHandler.show(update, context, message)

        elif target_menu == MenuLevel.ADMIN:
            from .admin_menu import AdminMenuHandler
            return await AdminMenuHandler.show(update, context, message)

        elif target_menu == MenuLevel.SETTINGS:
            from .settings_menu import SettingsMenuHandler
            return await SettingsMenuHandler.show(update, context, message)

        else:
            from .main_menu import MainMenuHandler
            return await MainMenuHandler.show(update, context, 'Произошла ошибка навигации')

    @staticmethod
    async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[MenuLevel]:
        current_menu = context.user_data.get('current_menu')

        if not current_menu:
            return await NavigationManager.go_to_menu(update, context, MenuLevel.MAIN)

        target_menu = NavigationState.get_back_target(current_menu)

        if target_menu:
            return await NavigationManager.go_to_menu(
                update,
                context,
                target_menu,
                f"↩️ Возврат из {current_menu.value}"
            )
        else:
            return current_menu

    @staticmethod
    def get_back_button(current_level: MenuLevel) -> Optional[InlineKeyboardButton]:
        target = NavigationState.get_back_target(current_level)

        if not target:
            return None

        button_texts = {
            MenuLevel.MAIN: "Главное меню",
            MenuLevel.SLOTS: "К слотам",
            MenuLevel.APPOINTMENTS: "К встречам",
            MenuLevel.ADMIN: "К админке"
        }

        return InlineKeyboardButton(
            f"↩️ {button_texts.get(target, 'Назад')}",
            callback_data=f'back_to_{target.value}'
        )

    @staticmethod
    def get_breadcrumbs_keyboard(current_level: MenuLevel) -> InlineKeyboardMarkup:
        breadcrumbs = NavigationState.get_breadcrumbs(current_level)

        if len(breadcrumbs) <= 1:
            return None

        keyboard = []
        row = []

        for i, level in enumerate(breadcrumbs):
            if i == len(breadcrumbs) - 1:
                continue

            level_names = {
                MenuLevel.MAIN: "🏠 Главная",
                MenuLevel.SLOTS: "⏰ Слоты",
                MenuLevel.APPOINTMENTS: "📅 Встречи",
                MenuLevel.ADMIN: "⚙️ Админка"
            }

            row.append(
                InlineKeyboardButton(
                    level_names.get(level, level.value),
                    callback_data=f'nav_to_{level.value}'
                )
            )

            if len(row) == 2:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        return InlineKeyboardMarkup(keyboard) if keyboard else None

    @staticmethod
    async def return_to_view_slots(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str = None) -> int:
        from .view_slot import ViewSlotsHandler
        view_handler = ViewSlotsHandler()

        if 'return_from_edit' in context.user_data:
            return_data = context.user_data.pop('return_from_edit')

            if return_data['handler'] == 'view_slots':
                if 'view_slots' in context.user_data:
                    context.user_data['view_slots']['current_page'] = return_data['page']

                    success_msg = "✅ Слот успешно обновлен!"
                    if message:
                        success_msg = f"{success_msg}\n{message}"

                    return await view_handler.show_slots_list(update, context)

                    # Если не было сохраненного состояния, просто запускаем заново


                return await view_handler.start(update, context)


