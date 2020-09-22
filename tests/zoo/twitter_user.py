from typing import List

from bson import ObjectId

from odmantic import Model


class TwitterUser(Model):
    """Self referencing model with manual reference handling"""

    following: List[ObjectId] = []
