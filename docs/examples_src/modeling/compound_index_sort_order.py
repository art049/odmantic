from datetime import datetime

from odmantic import Index, Model
from odmantic.query import asc, desc


class Event(Model):
    username: str
    date: datetime

    model_config = {"indexes": lambda: [Index(asc(Event.username), desc(Event.date))]}
