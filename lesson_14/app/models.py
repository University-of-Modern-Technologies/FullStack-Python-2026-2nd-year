from typing import Any, ClassVar

from mongoengine import *

from config import MONGODB_DB, MONGODB_HOST


connect(db=MONGODB_DB, host=MONGODB_HOST)


class Task(Document):
    objects: ClassVar[Any]

    completed = BooleanField(default=False)
    consumer = StringField(max_length=150)
