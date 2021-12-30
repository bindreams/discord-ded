import re
import os
from datetime import date, datetime, timedelta
from discord import File
from discord.ext import commands
import yaml
from .report import Report, this_month, format_day



class Bot(commands.Bot):
    prefix = "/"
    _re_lesson_command = re.compile(
        r"{prefix}lesson ([+-]=) (\d+)\.(\d+)\.(\d+) (\d+):(\d+):(\d+)\s*$".format(prefix=prefix)
    )

    NoMessage = object()

    def __init__(self):
        help_command = commands.DefaultHelpCommand(
            no_category = 'Commands'
        )

        super().__init__(command_prefix=self.prefix, help_command=help_command)
        self._report_channel = None
        self._lesson_channel = None
        self.current_lesson_start = None

        with open("/etc/discord-ded.conf", "r") as f:
            data = yaml.safe_load(f)
            self.report_channel_id = data["report_channel_id"]
            self.lesson_channel_id = data["lesson_channel_id"]

        @self.command(brief="Display bot status")
        async def status(ctx):
            if self.current_lesson_start is None:
                lesson_info = f"Занятие не идет"
            else:
                seconds = round((datetime.now() - self.current_lesson_start).total_seconds())
                lesson_info = f"Занятие в процессе ({timedelta(seconds=seconds)})"

            channel_info = f"Человек в канале: {len(self.lesson_channel.members)}"

            text = f"Дед жив\n{channel_info}\n{lesson_info}"
            await ctx.send(text)

        @self.command(brief="Scare the bot")
        async def scare(ctx):
            await ctx.send("Вы напугали деда")

        @self.command(brief="Display a motivational messge")
        async def motivate(ctx):
            data_dir = os.path.dirname(__file__) + "/data/"

            with open(data_dir + 'motivate.png', 'rb') as f:
                picture = File(f)
                await ctx.send(file=picture)

        @self.command(brief="Manually update lesson records")
        async def lesson(ctx):
            text = ctx.message.content

            try:
                match = re.search(self._re_lesson_command, text)
                if match is None:
                    # Command structure does not match
                    raise ValueError("команда не соответствует формату")

                # Validate data
                year = int(match[4])
                if year < 100:
                    year += 2000

                month = int(match[3])
                day = int(match[2])

                hours = int(match[5])
                minutes = int(match[6])
                seconds = int(match[7])

                if not 2020 <= year < 2050:
                    raise ValueError("подозрительный год")

                substract = (match[1] == "-=")

                if not 0 <= hours < 24:
                    raise ValueError("неверное значение для часов")

                if not 0 <= minutes < 60:
                    raise ValueError("неверное значение для минут")

                if not 0 <= seconds < 60:
                    raise ValueError("неверное значение для секунд")

                when = date(year, int(match[3]), int(match[2]))
                duration = timedelta(hours=int(match[5]), minutes=int(match[6]), seconds=int(match[7])).total_seconds()

            except ValueError as err:
                await ctx.send(
                    f"Не понял команду. ({err})\n"
                    "Формат: `lesson += <дата> <длительность>`\n"
                    "Пример правильной команды: lesson += 26.12.21 1:36:40"
                )
                return

            report = await self.record_lesson(when, duration, substract)
            if when in report.lessons:
                await ctx.send(format_day(when, report.lessons[when]))
            else:
                await ctx.send(f"No lessons on {when.day:02d}.{when.month:02d}.{when.year%100:02d}")

    @property
    def report_channel(self):
        """Text channel for report messages."""
        if self._report_channel is None:
            self._report_channel = self.get_channel(self.report_channel_id)

        return self._report_channel

    @property
    def lesson_channel(self):
        """Voice channel where lessons are tracked."""
        if self._lesson_channel is None:
            self._lesson_channel = self.get_channel(self.lesson_channel_id)

        return self._lesson_channel

    async def record_lesson(self, when, duration, substract=False):
        """Record a lesson at a date `when`, with `duration` in seconds.
        If `substract` is True, then this function substracts this time from the records.
        Returns the report in which the lesson was recorded. Note that if the lesson is substracted from a date for
        which there is no report, this report is created but not posted anywhere.
        """
        month = date(when.year, when.month, 1)
        report, message = await self.get_report(month)

        if substract:
            if when not in report.lessons:
                return report

            report.lessons[when] -= duration
            if report.lessons[when] <= 0:
                report.lessons.pop(when)
        else:
            if when not in report.lessons:
                report.lessons[when] = 0

            report.lessons[when] += duration

        await self.post_report(report, message)
        return report

    async def get_report(self, when):
        """Retrieve a report from the records or create a new one.
        Returns the Report object with date of `when` and the message in which the report was found.
        If the report was just created, returns self.NoMessage instead of message.
        """
        async for message in self.report_channel.history(limit=100):
            try:
                report = Report.fromstr(message.content)
            except:
                continue

            if report.date == when:
                return report, message

        return Report(when), self.NoMessage

    async def post_report(self, report, message=None):
        """Post the report in the report channel.
        If message is specified, edits the message with new information. Otherwise, tries to find the old report to
        edit it, or just sends a new message.
        """
        if message is None:
            _, message = await self.get_report(report.date)

        if message is self.NoMessage:
            await self.report_channel.send(str(report))
        else:
            await message.edit(content=str(report))

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_voice_state_update(self, member, before, after):
        """If 2 or more people join self.lesson_channel, start tracking the lesson. When one leaves, stops tracking."""

        print("Voice state update:")
        if before.channel == after.channel:
            print("  Channel didn't change")
            return

        if after.channel == self.lesson_channel:
            print(f"  Someone joined, now {len(self.lesson_channel.members)}")
            # Someone joined the channel
            if len(self.lesson_channel.members) >= 2 and self.current_lesson_start is None:
                self.current_lesson_start = datetime.now()

        if before.channel == self.lesson_channel:
            print(f"  Someone left, now {len(self.lesson_channel.members)}")
            # Someone left the channel
            if len(self.lesson_channel.members) < 2 and self.current_lesson_start is not None:
                lesson_duration = round((datetime.now() - self.current_lesson_start).total_seconds())
                self.current_lesson_start = None
                await self.record_lesson(date.today(), lesson_duration)
