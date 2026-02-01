from src.infrastructure.telegrambot.bot import BotApplication

def main():
    tg_app = BotApplication()
    tg_app.run()


if __name__ == '__main__':
    main()