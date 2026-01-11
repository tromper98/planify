from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_main_menu():
    keyboard = [
        [InlineKeyboardButton('📅 Расписание на сегодня', callback_data='admin_schedule_today')],
        [InlineKeyboardButton('📋 Все запланированные встречи', callback_data='admin_all_scheduled_appointment')],
        [InlineKeyboardButton('➕ Запланировать встречу', callback_data='admin_schedule_new_appointment')],
        [InlineKeyboardButton('🔔 Настройка уведомлений', callback_data='admin_notification_settings')],
    ]

    return InlineKeyboardMarkup(keyboard)


def get_admin_appointment_menu(appointment_id: int):
    keyboard = [
        [InlineKeyboardButton('✅ Подтвердить', callback_data=f'admin_confirm_{appointment_id}')],
        [InlineKeyboardButton('❌ Отклонить', callback_data=f'admin_reject_{appointment_id}')],
        [InlineKeyboardButton('✏️ Редактировать', callback_data=f'admin_edit_{appointment_id}')],
        [InlineKeyboardButton('📅 Перенести', callback_data=f'admin_reschedule_{appointment_id}')],
        [InlineKeyboardButton('🔙 Назад', callback_data='admin_back_to_list')],
    ]
    return InlineKeyboardMarkup(keyboard)
