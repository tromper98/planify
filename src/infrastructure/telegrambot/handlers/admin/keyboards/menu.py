from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard(available_handlers: list[dict]) -> InlineKeyboardMarkup:
    """Создание главного меню"""
    keyboard = []

    for handler in available_handlers:
        keyboard.append([
            InlineKeyboardButton(
                handler['name'],
                callback_data=handler['id']
            )
        ])

    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel')]
    ])