import logging
import json
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
import joy
from ..base import Base
from .helpers import read_optional, write_optional

optional = [
    "title",
    "content",
    "state"
]


class Proof(Base):
    __tablename__ = "proof"

    id: Mapped[str] = mapped_column(String, primary_key=True, insert_default=joy.crypto.address)
    person_id: Mapped[str]
    state: Mapped[Optional[str]]
    title: Mapped[Optional[str]]
    content: Mapped[Optional[str]]
    thread: Mapped[Optional[str]]
    files: Mapped[Optional[str]]
    poll: Mapped[Optional[str]]
    created: Mapped[str] = mapped_column(insert_default=joy.time.now)
    updated: Mapped[str] = mapped_column(insert_default=joy.time.now)

    @staticmethod
    def write(data):
        _data = data.copy()
        
        thread = _data.get("thread", None)
        if thread is not None:
            _data["thread"] = json.dumps(thread)

        files = _data.get("files", None)
        if files is not None:
            _data["files"] = json.dumps(files)

        poll = _data.get("poll", None)
        if poll is not None:
            _data["poll"] = json.dumps(poll)
        
        return Proof(**_data)

    def to_dict(self):
        data = {
            "id": self.id,
            "person_id": self.person_id,
            "created": self.created,
            "updated": self.updated
        }

        thread = getattr(self, "thread", None)
        if thread is not None:
            data["thread"] = json.loads(thread)

        files = getattr(self, "files", None)
        if files is not None:
            data["files"] = json.loads(files)

        poll = getattr(self, "poll", None)
        if poll is not None:
            data["poll"] = json.loads(poll)

        read_optional(self, data, optional)
        return data

    def update(self, data):
        write_optional(self, data, optional)
        thread = data.get("thread")
        if thread != None:
            self.thread = json.dumps(thread)

        files = data.get("files")
        if files != None:
            self.files = json.dumps(files)

        poll = data.get("poll")
        if poll != None:
            self.poll = json.dumps(poll)

        self.updated = joy.time.now()