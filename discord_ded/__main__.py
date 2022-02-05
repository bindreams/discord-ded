import sys
from argparse import ArgumentParser
from pathlib import Path

import yaml

import discord_ded

from .bot import Bot


def main():
    parser = ArgumentParser(
        "discord-ded", description="A Discord lesson counting bot.")
    parser.add_argument("-V", "--version", action='version',
                        version=discord_ded.__version__)
    parser.add_argument("-c", "--config", type=Path,
                        default=Path("discord-ded.conf"), help="Path to the config file.")

    args = parser.parse_args()

    if not args.config.exists():
        print(
            f"Could not find a config file '{args.config}'. Create the config file or specify path with --config.")
        return 1

    with open(args.config, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    bot = Bot(
        report_channel_id=data["report_channel_id"],
        lesson_channel_id=data["lesson_channel_id"]
    )
    bot.run(data["bot_token"])


if __name__ == "__main__":
    sys.exit(main())
