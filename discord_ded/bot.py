import re
from discord.ext import commands
from auth import bot_token, report_channel_id, lesson_channel_id
from report import Report, this_month, format_day
from datetime import date, datetime, timedelta


class Bot(commands.Bot):
    _re_lesson_command = re.compile(r"!lesson ([+-]=) (\d+)\.(\d+)\.(\d+) (\d+):(\d+):(\d+)")

    NoMessage = object()

    def __init__(self):
        super().__init__(command_prefix="!")
        self._report_channel = None
        self._lesson_channel = None
        self.current_lesson_start = None

        @self.command()
        async def status(ctx):
            if self.current_lesson_start is None:
                lesson_info = "Занятие не идет"
            else:
                seconds = round((datetime.now() - self.current_lesson_start).total_seconds())
                lesson_info = f"Занятие в процессе ({timedelta(seconds=seconds)})"

            text = f"Дед жив\n{lesson_info}"
            await ctx.send(text)

        @self.command()
        async def lesson(ctx):
            text = ctx.message.content
            try:
                match = re.search(self._re_lesson_command, text)
            except:
                ctx.send(
                    "Не понял команду.\n"
                    "Пример правильной команды: lesson += 26.12.21 1:36:40"
                )
            
            if int(match[4]) > 2000:
                year = int(match[4])
            else:
                year = 2000 + int(match[4])
            
            when = date(year, int(match[3]), int(match[2]))
            duration = timedelta(hours=int(match[5]), minutes=int(match[6]), seconds=int(match[7])).total_seconds()

            report = await self.record_lesson(when, duration, (match[1] == "-="))
            if when in report.lessons:
                await ctx.send(format_day(when, report.lessons[when]))
            else:
                await ctx.send(f"No lessons on {when.day:02d}.{when.month:02d}.{when.year%100:02d}")
            
    
    @property
    def report_channel(self):
        if self._report_channel is None:
            self._report_channel = self.get_channel(report_channel_id)
        
        return self._report_channel
    
    @property
    def lesson_channel(self):
        if self._lesson_channel is None:
            self._lesson_channel = self.get_channel(lesson_channel_id)
        
        return self._lesson_channel

    async def record_lesson(self, when, duration, substract=False):
        month = date(when.year, when.month, 1)
        report, message = await self.get_report(month)

        if substract:
            if when not in report.lessons:
                return

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
        async for message in self.report_channel.history(limit=10):
            try:
                report = Report.fromstr(message.content)
            except:
                continue
            
            if report.date == when:
                return report, message
        
        return Report(), self.NoMessage
    
    async def post_report(self, report, message=None):
        if message is None:
            _, message = await self.get_report(report.date)

        if message is self.NoMessage:
            await self.report_channel.send(str(report))
        else:
            await message.edit(content=str(report))

    async def on_ready(self):
        print(f'Logged on as {self.user}!')
    
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        
        if after.channel == self.lesson_channel:
            # Someone joined the channel
            if len(self.lesson_channel.members) >= 2 and self.current_lesson_start is None:
                self.current_lesson_start = datetime.now()
        
        if before.channel == self.lesson_channel:
            # Someone left the channel
            if len(self.lesson_channel.members) < 2 and self.current_lesson_start is not None:
                lesson_duration = round((datetime.now() - self.current_lesson_start).total_seconds())
                self.current_lesson_start = None
                await self.record_lesson(date.today(), lesson_duration)
        

def main():
    bot = Bot()
    bot.run(bot_token)

if __name__ == "__main__":
    main()
