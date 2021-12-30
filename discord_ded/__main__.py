import sys
import yaml
from .bot import Bot
from .keepalive import keepalive

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--keep-alive":
        keepalive()

    with open("/etc/discord-ded.conf", "r") as f:
        data = yaml.safe_load(f)

    bot = Bot()
    bot.run(data["bot_token"])

if __name__ == "__main__":
    main()
