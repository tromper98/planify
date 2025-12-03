from app import tg_handler
from telegram.ext import ApplicationBuilder, CommandHandler

from infrastructure.envconfig import EnvConfig


if __name__ == '__main__':
    application = ApplicationBuilder().token(EnvConfig.get_str('TG_BOT_TOKEN')).build()

    start_handler = CommandHandler('start', tg_handler.start)

    application.add_handler(start_handler)

    application.run_polling()