import logging
from typing import Type, TypeVar
from enum import Enum

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters

from src.common.utils.validators import *
from src.app.models.role import Role
from src.app.services import RoleService, SlotService
from src.infrastructure.postgres.databaseengine import DatabaseEngine
from src.infrastructure.telegrambot.handlers.admin.menu.states import MenuLevel
from src.infrastructure.telegrambot.handlers.admin.menu import NavigationManager
from src.infrastructure.telegrambot.handlers.admin.keyboards import *


from .base import BaseHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

Context = TypeVar('Context', bound=ContextTypes.DEFAULT_TYPE)

class ViewSlotsStates(Enum):
    SHOW_LIST = 1
    SLOT_DETAILS = 2
    FILTER_SLOTS = 3
    SORT_SLOTS = 4

class ViewSlotsHandler(BaseHandler):

    def __init__(self):
        super().__init__("view_slots")
        self.item_per_page = 5

    def define_states(self) -> Type[Enum]:
        return ViewSlotsStates

    def is_available_for_user(self, user_id: int) -> bool:
        role: Role = RoleService(DatabaseEngine()).get_user_role_by_tg_id(user_id)
        return role == Role.ADMIN

    def get_conversation_handler(self) -> ConversationHandler:
        con_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start, pattern='^view_slots$'),
                CallbackQueryHandler(self.show_slot_details, pattern='^slot_details_\d+$')
            ],
            states={
                ViewSlotsStates.SHOW_LIST: [
                    CallbackQueryHandler(self.handle_list_action, pattern='^(page_\d+|filter|sort|refresh|back_to_list)$'),
                    CallbackQueryHandler(self.show_slot_details, pattern='^view_slot_\d+$'),
                    CallbackQueryHandler(self.handle_quick_action, pattern='^(edit_slot_\d+|delete_slot_\d+|clone_slot_\d+)$')
                    ],
                ViewSlotsStates.FILTER_SLOTS: [
                    CallbackQueryHandler(self.apply_filter, pattern='^filter_(all|active|past|future|cancel)$'),
                    CallbackQueryHandler(self.cancel_filter, pattern='^cancel_filter$')
                ],
                ViewSlotsStates.SORT_SLOTS: [
                    CallbackQueryHandler(self.apply_sort, pattern='^sort_(date_asc|date_desc|time_asc|time_desc|cancel)$')
                ]
            },
            fallbacks=[
                CallbackQueryHandler(self.cancel_view, pattern='^cancel_view$'),
                MessageHandler(filters.Regex('^/cancel$'), self.cancel_view),
                CallbackQueryHandler(
                    lambda u, c: NavigationManager.go_to_menu(u, c, MenuLevel.SLOTS, "↩️ Возврат к управлению слотами"),
                    pattern='^back_to_slots_menu$'
                )
            ],
            map_to_parent={
                ConversationHandler.END: ConversationHandler.END
            }
        )
        return con_handler

    async def start(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        user_id =update.effective_user.id

        context.user_data['view_slots'] = {
            'user_id': user_id,
            'current_page': 0,
            'filter_type': 'active',
            'sort_by': 'date_asc',
            'last_active': 'list'
        }

        slots = self._get_slot_for_user(context)

        if not slots:
            return await self.show_empty_state(update, context)

        return await self.show_slots_list(update, context)

    async def show_slots_list(self, update: Update, context: Context, slots: list[dict] = None):
        if slots is None:
            slots = self._get_slots_for_user(context)

        if not slots:
            return await self.show_empty_state(update, context)

        view_data = context.user_data['view_slots']
        current_page = view_data['current_page']
        total_pages = (len(slots) + self.item_per_page - 1) // self.item_per_page

        start_idx = current_page * self.item_per_page
        end_idx = start_idx + self.item_per_page
        page_slots = slots[start_idx:end_idx]

        message_text = self._format_list_message(page_slots, current_page, total_pages, view_data)

        keyboard = get_slots_list_keyboard(
            slots=page_slots,
            current_page=current_page,
            total_pages=total_pages,
            filter_type=view_data['filter_type'],
            sort_by=view_data['sort_by']
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )

        view_data['last_action'] = 'list'
        return ViewSlotsStates.SHOW_LIST

    async def show_slot_details(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        if query.data.startswith('slot_details_'):
            slot_id = int(query.data.split('_')[2])
        else:
            slot_id = int(query.data.split('_')[2])


        slot_service = SlotService(DatabaseEngine())
        slot = slot_service.get_slot_by_id(slot_id)
        if not slot:
            await query.edit_message_text(
                "❌ Слот не найден или у вас нет к нему доступа.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("↩️ К списку слотов", callback_data='back_to_list')]
                ])
            )
            return ViewSlotsStates.SHOW_LIST

        context.user_data['view_slots']['current_slot_id'] = slot_id

        message_text = self._format_slot_details(slot)
        role_service = RoleService(DatabaseEngine())

        keyboard = get_slot_details_keyboard(
            slot_id=slot_id,
            slot_status=slot.get('status', 'active'),
            user_role=role_service.get_user_role_by_tg_id(update.effective_user.id),
            include_back=True
        )

        nav_buttons = []
        if self._has_previous_slot(context, slot_id):
            nav_buttons.append(InlineKeyboardButton("⬅️ Предыдущий", callback_data=f'view_slot_{slot_id - 1}'))

        if self._has_next_slot(context, slot_id):
            nav_buttons.append(InlineKeyboardButton("Следующий ➡️", callback_data=f'view_slot_{slot_id + 1}'))

        if nav_buttons:
            keyboard.inline_keyboard.append(nav_buttons)

        await query.edit_message_text(
            text=message_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )

        context.user_data['view_slots']['last_action'] = 'details'
        return ViewSlotsStates.SLOT_DETAILS


    async def handle_list_action(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        action = query.data
        view_data = context.user_data['view_slots']

        if action.startswith('page_'):
            page_num = int(action.split('_')[1])
            view_data['current_page'] = page_num
            return await self.show_slots_list(update, context)

        elif action == 'filter':
            return await self.show_filter_menu(update, context)

        elif action == 'sort':
            return await self.show_sort_menu(update, context)

        elif action == 'refresh':
            return await self.show_slots_list(update, context)

        elif action == 'back_to_list':
            return await self.show_slots_list(update, context)

        return ViewSlotsStates.SHOW_LIST

    async def handle_slot_action(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        action = query.data

        if action.startswith('edit_slot_'):
            slot_id = int(action.split('_')[2])
            return await self.start_edit_slot(update, context, slot_id)

        elif action.startswith('delete_slot_'):
            slot_id = int(action.split('_'[2]))
            return await self.start_delete_slot(update, context, slot_id)

        elif action.startswith('back_to_list'):
            return await self.show_slots_list(update, context)

        return ViewSlotsStates.SLOT_DETAILS

    async def handle_quick_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        action = query.data

        if action.startswith('edit_slot_'):
            slot_id = int(action.split('_')[2])
            from src.infrastructure.telegrambot.handlers.admin.actions.edit_slot import EditSlotHandler
            edit_handler = EditSlotHandler()
            return await edit_handler.start_with_slot(update, context, slot_id)

        elif action.startswith('delete_slot_'):
            slot_id = int(action.split('_')[2])
            return await self.show_delete_confirmation(update, context, slot_id)

        return ViewSlotsStates.SHOW_LIST

    async def show_filter_menu(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        view_data = context.user_data['view_slots']
        current_filter = view_data['filter_type']

        filter_options = [
            ('all', 'Все слоты', '🌐'),
            ('active', 'Активные', '✅'),
            ('future', 'Будущие', '📅'),
            ('past', 'Прошедшие', '⏳'),
            ('cancel', 'Отмененные', '❌')
        ]

        keyboard = []
        for filter_id, filter_name, icon in filter_options:
            is_current = '📍' if filter_id == current_filter else ''
            button_text = f"{icon} {filter_name} {is_current}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f'filter_{filter_id}')])

        keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='cancel_filter')])

        await query.edit_message_text(
            text="🔍 <b>Фильтрация слотов</b>\n\n"
                 "Выберите тип фильтра:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return ViewSlotsStates.FILTER_SLOTS

    async def apply_filter(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        filter_type = query.data.split('_')[1]
        context.user_data['view_slots']['filter_type'] = filter_type
        context.user_data['view_slots']['current_page'] = 0

        return await self.show_slots_list(update, context)

    async def cancel_filter(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        return await self.show_slots_list(update, context)

    async def show_sort_menu(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        view_data = context.user_data['view_slots']
        current_sort = view_data['sort_by']

        sort_options = [
            ('date_asc', 'По дате (сначала старые)', '📅⬆️'),
            ('date_desc', 'По дате (сначала новые)', '📅⬇️'),
            ('time_asc', 'По времени (рано → поздно)', '⏰⬆️'),
            ('time_desc', 'По времени (поздно → рано)', '⏰⬇️')
        ]

        keyboard = []
        for sort_id, sort_name, icon in sort_options:
            is_current = '📍' if sort_id == current_sort else ''
            button_text = f"{icon} {sort_name} {is_current}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f'sort_{sort_id}')])

        keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='sort_cancel')])

        await query.edit_message_text(
            text="🔢 <b>Сортировка слотов</b>\n\n"
                 "Выберите способ сортировки:",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return ViewSlotsStates.SORT_SLOTS

    async def apply_sort(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        sort_type = query.data.split('_')[1]

        if sort_type == 'cancel':
            return await self.show_slots_list(update, context)

        context.user_data['view_slots']['sort_by'] = sort_type
        context.user_data['view_slots']['current_page'] = 0

        return await self.show_slots_list(update, context)

    def _get_slots_for_user(self, context: Context) -> list[dict]:
        view_data = context.user_data['view_slots']
        user_id = view_data['user_id']

        all_slots = get_user_slots(user_id)

        filtered_slots = self._apply_filter(all_slots, view_data['filter_type'])
        sorted_slots = self._apply_sort(filtered_slots, view_data['sort_by'])

        return sorted_slots

    def _apply_filter(self, slots: list[dict], filter_type: str) -> list[dict]:
        now = datetime.now()

        if filter_type == 'all':
            return slots
        elif filter_type == 'active':
            return [s for s in slots if s.get('status') == 'active']
        elif filter_type == 'future':
            return [s for s in slots if self._is_future_slot(s, now)]
        elif filter_type == 'past':
            return [s for s in slots if not self._is_future_slot(s, now)]
        elif filter_type == 'cancel':
            return [s for s in slots if s.get('status') == 'cancelled']

        return slots


    def _apply_sort(self, slots: list[dict], sort_by: str) -> list[dict]:
        if sort_by == 'date_asc':
            return sorted(slots, key=lambda x: (x['date'], x['start_time']))
        elif sort_by == 'date_desc':
            return sorted(slots, key=lambda x: (x['date'], x['start_time']), reverse=True)
        elif sort_by == 'time_asc':
            return sorted(slots, key=lambda x: x['start_time'])
        elif sort_by == 'time_desc':
            return sorted(slots, key=lambda x: x['start_time'], reverse=True)

        return slots

    def _is_future_slot(self, slot: dict, now: datetime) -> bool:
        from datetime import datetime as dt
        slot_datetime = dt.combine(slot['date'], slot['start_time'])
        return slot_datetime > now

    def _has_previous_slot(self, context: Context, current_slot_id: int) -> bool:
        slots = self._get_slots_for_user(context)
        slot_ids = [s['slot_id'] for s in slots]
        current_index = slot_ids.index(current_slot_id) if current_slot_id in slot_ids else -1
        return current_index > 0

    def _has_next_slot(self, context: Context, current_slot_id: int) -> bool:
        slots = self._get_slots_for_user(context)
        slot_ids = [s['slot_id'] for s in slots]
        current_index = slot_ids.index(current_slot_id) if current_slot_id in slot_ids else -1
        return current_index < len(slot_ids) - 1 and current_index != -1

    async def show_another_slot(self, update: Update, context: Context):
        query = update.callback_query
        await query.answer()

        return await self.show_slot_details(update, context)

    def _format_list_message(self, slots: list[dict], current_page: int, total_pages: int, view_data: dict) -> str:
        filter_names = {
            'all': 'Все слоты',
            'active': 'Активные',
            'future': 'Будущие',
            'past': 'Прошедшие',
            'cancel': 'Отмененные'
        }

        sort_names = {
            'date_asc': 'по дате ↗️',
            'date_desc': 'по дате ↘️',
            'time_asc': 'по времени ↗️',
            'time_desc': 'по времени ↘️'
        }

        header = (
            f"⏰ <b>Ваши слоты</b>\n"
            f"📊 <i>Фильтр: {filter_names.get(view_data['filter_type'], 'Все')} | "
            f"Сортировка: {sort_names.get(view_data['sort_by'], 'по дате')}</i>\n"
            f"📄 Страница {current_page + 1} из {total_pages}\n"
        )

        if not slots:
            return f"{header}\n📭 Список пуст"

        slots_text = "\n".join([
            self._format_slot_list_item(slot, idx + current_page * self.items_per_page + 1)
            for idx, slot in enumerate(slots)
        ])

        return f"{header}\n\n{slots_text}"

    def _format_slot_list_item(self, slot: dict, index: int) -> str:
        date_str = slot['date'].strftime("%d.%m.%Y")
        time_str = slot['start_time'].strftime("%H:%M")
        duration = slot['duration']

        status_icons = {
            'active': '✅',
            'booked': '📅',
            'cancelled': '❌',
            'completed': '✔️'
        }

        status_icon = status_icons.get(slot.get('status', 'active'), '🔘')

        return (
            f"{index}. {status_icon} <b>{date_str} {time_str}</b> "
            f"({duration} мин) /slot_{slot['id']}"
        )

    def _format_slot_details(self, slot: dict) -> str:
        date_str = slot['date'].strftime("%d.%m.%Y")
        time_str = slot['start_time'].strftime("%H:%M")
        end_time = self._calculate_end_time(slot['start_time'], slot['duration'])
        created_str = slot['created_at'].strftime("%d.%m.%Y %H:%M") if slot.get('created_at') else "неизвестно"

        status_texts = {
            'active': '🟢 Активный',
            'booked': '📅 Забронирован',
            'cancelled': '🔴 Отменен',
            'completed': '✔️ Завершен'
        }

        status = status_texts.get(slot.get('status', 'active'), '❓ Неизвестно')

        return (
            f"📋 <b>Детали слота #{slot['id']}</b>\n\n"
            f"📅 <b>Дата:</b> {date_str}\n"
            f"⏰ <b>Время:</b> {time_str} - {end_time}\n"
            f"⏱️ <b>Длительность:</b> {slot['duration']} минут\n"
            f"📊 <b>Статус:</b> {status}\n"
            f"👤 <b>Создатель:</b> {slot.get('creator_name', 'Неизвестно')}\n"
            f"📝 <b>Описание:</b> {slot.get('description', 'нет')}\n"
            f"🕒 <b>Создан:</b> {created_str}\n"
        )

    def _calculate_end_time(self, start_time, duration_minutes):
        from datetime import datetime, timedelta
        start_dt = datetime.combine(datetime.today(), start_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        return end_dt.strftime("%H:%M")

    async def show_empty_state(self, update: Update, context: Context) -> int:
        keyboard = get_empty_slots_keyboard()

        message_text = (
            "📭 <b>У вас пока нет слотов</b>\n\n"
            "Создайте свой первый слот для планирования встреч!"
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                text=message_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )

        return ConversationHandler.END

    async def cancel_view(self, update: Update, context: Context):
        query = update.callback_query
        if query:
            await query.answer()

        if 'view_slots' in context.user_data:
            del context.user_data['view_slots']

        return await NavigationManager.go_to_menu(
            update,
            context,
            MenuLevel.SLOTS,
            "❌ Просмотр слотов отменен"
        )

    async def start_edit_slot(self, update: Update, context: Context, slot_id: int):
        """Начать редактирование слота"""
        from src.infrastructure.telegrambot.handlers.admin.actions.edit_slot import EditSlotHandler
        edit_handler = EditSlotHandler()

        # Сохраняем контекст для возврата
        context.user_data['return_from_edit'] = {
            'handler': 'view_slots',
            'slot_id': slot_id,
            'page': context.user_data['view_slots']['current_page']
        }

        return await edit_handler.start_with_slot(update, context, slot_id)

    async def start_delete_slot(self, update: Update, context: Context, slot_id: int):
        """Начать удаление слота"""
        from  src.infrastructure.telegrambot.handlers.admin.actions.delete_slot import DeleteSlotHandler
        delete_handler = DeleteSlotHandler()

        # Сохраняем контекст для возврата
        context.user_data['return_from_delete'] = {
            'handler': 'view_slots',
            'slot_id': slot_id,
            'page': context.user_data['view_slots']['current_page']
        }

        return await delete_handler.start_with_slot(update, context, slot_id)

    async def show_delete_confirmation(self, update: Update, context: Context, slot_id: int):
        """Показать подтверждение удаления"""
        query = update.callback_query
        await query.answer()

        slot_service = SlotService(DatabaseEngine())
        slot = slot_service.get_slot_by_id(slot_id)
        if not slot:
            await query.answer("Слот не найден", show_alert=True)
            return await self.show_slots_list(update, context)

        date_str = slot['date'].strftime("%d.%m.%Y")
        time_str = slot['start_time'].strftime("%H:%M")

        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f'confirm_delete_{slot_id}'),
                InlineKeyboardButton("❌ Нет, отменить", callback_data=f'cancel_delete_{slot_id}')
            ]
        ]

        await query.edit_message_text(
            text=f"🗑️ <b>Подтверждение удаления</b>\n\n"
                 f"Вы уверены, что хотите удалить слот?\n"
                 f"📅 {date_str} в {time_str}\n\n"
                 f"<i>Это действие нельзя отменить.</i>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return ViewSlotsStates.SHOW_LIST