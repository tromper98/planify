import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, CommandHandler

from src.infrastructure.env.envconfig import EnvConfig

from .handlers.admin.actions import *
from .handlers.admin.menu import *

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BotApplication:

    def __init__(self):
        self._token = EnvConfig.get_str('TG_BOT_TOKEN')
        self.application = Application.builder().token(self._token).build()

        self._init_handlers()

    def _init_handlers(self) -> None:

        # 1-st level Main Menu
        for handler in MainMenuHandler.get_handlers():
            self.application.add_handler(handler)

        # 2-nd level Menu's
        for handler in SlotMenuHandler().get_handlers():
            self.application.add_handler(handler)

        # Navigation Manager's
        self.application.add_handler(
            CallbackQueryHandler(
                lambda u, c: NavigationManager.go_back(u, c),
                pattern='^back$'
            )
        )

        # Action Handler's
        add_slot_handler = AddSlotHandler()
        self.application.add_handler(add_slot_handler.get_conversation_handler())


        # Base Command's
        self.application.add_handler(CommandHandler('help', self.show_help))
        self.application.add_handler(CommandHandler('cancel', self.cancel_command))

        # Unknown Command
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.unknown_command))

    async def show_help(self, update: Update, context):
        help_text = (
            "🤖 **Помощь по боту**\n\n"
            "Доступные команды:\n"
            "/start - Главное меню\n"
            "/menu - Вернуться в меню\n"
            "/help - Эта справка\n"
            "/cancel - Отменить текущее действие\n\n"
            "📞 Техподдержка: @support_username"
        )

        keyboard = [
            [InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')]
        ]

        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


    async def cancel_command(self, update: Update, context):
        """Отмена текущего действия"""
        await update.message.reply_text(
            "❌ Действие отменено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 В главное меню", callback_data='back_to_main')]
            ])
        )


    async def unknown_command(self, update: Update, context):
        """Обработка неизвестных сообщений"""
        await update.message.reply_text(
            "Я не понимаю эту команду. Используйте /menu для вызова меню.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 В меню", callback_data='back_to_main')]
            ])
        )


    def run(self):
        print("🤖 Бот запущен с многоуровневым меню...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

#
# def start_tg_bot():
#     application = Application.builder().token(EnvConfig.get_str('TG_BOT_TOKEN')).build()
#
#     register_handlers(application)
#
#     application.run_polling(allowed_updates=Update.ALL_TYPES)
#
#
# def register_handlers(app: Application) -> None:
#     menu_handler = MainMenuHandler()
#     add_slot_handler = AddSlotHandler()
#
#
#     for handler in menu_handler.get_handlers():
#         app.add_handler(handler)
#
#     app.add_handler(
#         CallbackQueryHandler(
#             menu_handler.show_main_menu,
#             pattern='^menu$'
#         )
#     )
#
#     app.add_handler(add_slot_handler.get_conversation_handler())
