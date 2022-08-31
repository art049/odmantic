from typing import List

from odmantic.model import Model


class Student(Model):
    scores: List[int]
