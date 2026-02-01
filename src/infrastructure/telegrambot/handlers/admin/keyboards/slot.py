from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict

from src.app.models.role import Role


def get_slots_menu_keyboard(actions: List[Dict]) -> InlineKeyboardMarkup:
    """Клавиатура меню управления слотами (уровень 2)"""
    keyboard = []

    # Группируем кнопки по 2 в ряд для лучшего вида
    for i in range(0, len(actions), 2):
        row = []
        for j in range(2):
            if i + j < len(actions):
                action = actions[i + j]
                row.append(
                    InlineKeyboardButton(
                        f"{action.get('icon', '')} {action['name']}",
                        callback_data=action['id']
                    )
                )
        if row:
            keyboard.append(row)

    # Добавляем кнопки навигации
    keyboard.append([
        InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main'),
        InlineKeyboardButton("📋 Быстрые действия", callback_data='quick_actions')
    ])

    return InlineKeyboardMarkup(keyboard)


def get_slot_details_keyboard(slot_id: int, slot_status: str, user_role: Role,
                              include_back: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для деталей слота"""
    keyboard = []

    # Основные действия
    if slot_status == 'active':
        if user_role in [Role.ADMIN, Role.CLIENT]:
            keyboard.append([
                InlineKeyboardButton("✏️ Редактировать", callback_data=f'edit_slot_{slot_id}'),
                InlineKeyboardButton("📋 Копировать", callback_data=f'clone_slot_{slot_id}')
            ])

        keyboard.append([
            InlineKeyboardButton("📅 Забронировать", callback_data=f'book_slot_{slot_id}'),
            InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_slot_{slot_id}')
        ])

    elif slot_status == 'booked':
        keyboard.append([
            InlineKeyboardButton("🚫 Отменить бронь", callback_data=f'cancel_booking_{slot_id}'),
            InlineKeyboardButton("📋 Детали брони", callback_data=f'booking_details_{slot_id}')
        ])

    # Кнопка возврата
    if include_back:
        keyboard.append([
            InlineKeyboardButton("↩️ К списку", callback_data='back_to_list')
        ])

    return InlineKeyboardMarkup(keyboard)


def get_pagination_keyboard(current_page: int, total_pages: int,
                            prefix: str = 'page') -> List[List[InlineKeyboardButton]]:
    """Клавиатура пагинации"""
    if total_pages <= 1:
        return []

    max_buttons = 5  # Максимум кнопок на странице
    half_max = max_buttons // 2

    # Определяем диапазон страниц для отображения
    start_page = max(0, current_page - half_max)
    end_page = min(total_pages, start_page + max_buttons)

    # Корректируем начальную страницу, если мы в конце списка
    if end_page - start_page < max_buttons:
        start_page = max(0, end_page - max_buttons)

    buttons = []

    # Кнопка первой страницы
    if start_page > 0:
        buttons.append(InlineKeyboardButton("1", callback_data=f'{prefix}_0'))
        if start_page > 1:
            buttons.append(InlineKeyboardButton("...", callback_data='noop'))

    # Кнопки страниц
    for page in range(start_page, end_page):
        if page == current_page:
            buttons.append(InlineKeyboardButton(f"[{page + 1}]", callback_data=f'{prefix}_{page}'))
        else:
            buttons.append(InlineKeyboardButton(str(page + 1), callback_data=f'{prefix}_{page}'))

    # Кнопка последней страницы
    if end_page < total_pages:
        if end_page < total_pages - 1:
            buttons.append(InlineKeyboardButton("...", callback_data='noop'))
        buttons.append(InlineKeyboardButton(str(total_pages), callback_data=f'{prefix}_{total_pages - 1}'))

    # Кнопки навигации
    nav_row = []
    if current_page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'{prefix}_{current_page - 1}'))

    if current_page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Вперед ➡️", callback_data=f'{prefix}_{current_page + 1}'))

    return [buttons, nav_row] if nav_row else [buttons]


def get_empty_slots_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для пустого списка слотов"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Создать слот", callback_data='add_slot'),
            InlineKeyboardButton("📋 Импорт", callback_data='import_slots')
        ],
        [
            InlineKeyboardButton("📚 Справка", callback_data='slots_help'),
            InlineKeyboardButton("↩️ К меню", callback_data='back_to_slots_menu')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_filter_keyboard(current_filter: str) -> InlineKeyboardMarkup:
    """Клавиатура фильтров"""
    filters = [
        ('all', 'Все слоты', '🌐'),
        ('active', 'Активные', '✅'),
        ('future', 'Будущие', '📅'),
        ('past', 'Прошедшие', '⏳'),
        ('booked', 'Забронированные', '📋'),
        ('cancelled', 'Отмененные', '❌')
    ]

    keyboard = []
    for filter_id, filter_name, icon in filters:
        is_active = ' ✅' if filter_id == current_filter else ''
        button_text = f"{icon} {filter_name}{is_active}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'filter_{filter_id}')])

    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='cancel_filter')])

    return InlineKeyboardMarkup(keyboard)


def get_slots_list_keyboard(slots: List[Dict], current_page: int, total_pages: int,
                            filter_type: str, sort_by: str) -> InlineKeyboardMarkup:
    """Клавиатура для списка слотов"""
    keyboard = []

    # Кнопки для каждого слота
    for slot in slots:
        date_str = slot['date'].strftime("%d.%m")
        time_str = slot['start_time'].strftime("%H:%M")

        button_text = f"📅 {date_str} {time_str} ({slot['duration']} мин)"
        callback_data = f"view_slot_{slot['id']}"

        # Быстрые действия
        quick_actions = [
            InlineKeyboardButton("✏️", callback_data=f"edit_slot_{slot['id']}"),
            InlineKeyboardButton("🗑️", callback_data=f"delete_slot_{slot['id']}"),
            InlineKeyboardButton("📋", callback_data=f"clone_slot_{slot['id']}")
        ]

        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=callback_data)
        ])
        keyboard.append(quick_actions)

    # Кнопки фильтрации и сортировки
    filter_buttons = [
        InlineKeyboardButton("🔍 Фильтр", callback_data='filter'),
        InlineKeyboardButton("🔢 Сортировка", callback_data='sort'),
        InlineKeyboardButton("🔄 Обновить", callback_data='refresh')
    ]
    keyboard.append(filter_buttons)

    # Пагинация
    if total_pages > 1:
        pagination_row = []

        if current_page > 0:
            pagination_row.append(
                InlineKeyboardButton("⬅️ Предыдущая", callback_data=f'page_{current_page - 1}')
            )

        if current_page < total_pages - 1:
            pagination_row.append(
                InlineKeyboardButton("Следующая ➡️", callback_data=f'page_{current_page + 1}')
            )

        if pagination_row:
            keyboard.append(pagination_row)

    # Навигационные кнопки
    navigation_row = [
        InlineKeyboardButton("↩️ К меню слотов", callback_data='back_to_slots_menu'),
        InlineKeyboardButton("❌ Отмена", callback_data='cancel_view')
    ]
    keyboard.append(navigation_row)

    return InlineKeyboardMarkup(keyboard)