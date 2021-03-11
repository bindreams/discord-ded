import sys
from .bot import Bot
from .auth import bot_token
from .keepalive import keepalive

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--keep-alive":
        keepalive()

    bot = Bot()
    bot.run(bot_token)

if __name__ == "__main__":
    main()
