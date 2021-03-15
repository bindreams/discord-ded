import re
from datetime import date, time, timedelta
from sortedcontainers import SortedDict


def this_month():
    """a datetime.date that represents day 1 of current month."""
    today = date.today()
    return date(today.year, today.month, 1)


def format_day(when, duration):
    """Format a day of lessons as `dd.mm.yy: n занятий (H:mm:ss)`."""
    lesson_count = round(duration / Report.lesson_duration)

    if lesson_count == 1:
        word_form = "занятие"
    elif lesson_count in (2, 3, 4):
        word_form = "занятия"
    else:
        word_form = "занятий"

    return (
        f"{when.day:02d}.{when.month:02d}.{when.year%100:02d}: " +
        f"{lesson_count} {word_form} ({timedelta(seconds=duration)})"
    )


class Report:
    """A record of all lessons in one month."""
    lesson_duration = 60*60*1.5  # 1.5 hrs in seconds

    _re_title = re.compile(r"Занятия (\d+)\.(\d+) \(всего (\d+)\):")
    _re_lesson = re.compile(r"(\d+).(\d+).(\d+): (\d+) заняти[еяй] \((\d+):(\d+):(\d+)\)")

    def __init__(self, date=None):
        self.date = date or this_month()

        self.lessons = SortedDict()
    
    @classmethod
    def fromstr(cls, text):
        self = cls()
        
        lines = text.split("\n")
        title = lines[0]
        lesson_lines = lines[2:]

        match = re.search(self._re_title, title)
        self.date = date(2000 + int(match[2]), int(match[1]), 1)

        for line in lesson_lines:
            match = re.search(self._re_lesson, line)

            when = date(2000 + int(match[3]), int(match[2]), int(match[1]))
            duration = timedelta(hours=int(match[5]), minutes=int(match[6]), seconds=int(match[7])).total_seconds()

            self.lessons[when] = duration
            
        return self

    def merge(self, other):
        if self.date != other.date:
            raise ValueError("Merging reports from different months")

        for lesson in other.lessons:
            if lesson in self.lessons:
                self.lessons[lesson] = self.lessons[lesson] + other.lessons[lesson]
            else:
                self.lessons[lesson] = other.lessons[lesson]
        
        return self

    @property
    def total_time(self):
        return sum(time for time in self.lessons.values())
    
    @property
    def total_lessons(self):
        return round(self.total_time / self.lesson_duration)

    def __str__(self):
        title = f"Занятия {self.date.month:02d}.{self.date.year%100:02d} (всего {self.total_lessons}):\n\n"

        lesson_lines = []
        for when, duration in self.lessons.items():
            lesson_lines.append(format_day(when, duration))
        
        return title + "\n".join(lesson_lines)
