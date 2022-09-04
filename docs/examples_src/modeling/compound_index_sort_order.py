from datetime import datetime

from odmantic import Index, Model
from odmantic.query import asc, desc


class Event(Model):
    username: str
    date: datetime

    class Config:
        @staticmethod
        def indexes():
            yield Index(asc(Event.username), desc(Event.date))
