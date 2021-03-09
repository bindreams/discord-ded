from .bot import Bot
from .auth import bot_token


def main():
    bot = Bot()
    bot.run(bot_token)

if __name__ == "__main__":
    main()
