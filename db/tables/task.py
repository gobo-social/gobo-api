import logging
import json
from typing import Optional
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
import joy
from ..base import Base
from .helpers import read_optional, write_optional

optional = [
    "channel",
    "shard",
    "name",
    "priority",    
    "tries",
    "failure",
]

class Task(Base):
    __tablename__ = "task"

    id: Mapped[str] = mapped_column(String, primary_key=True, insert_default=joy.crypto.address)
    channel: Mapped[Optional[str]]
    shard: Mapped[Optional[int]]
    name: Mapped[Optional[str]]
    priority: Mapped[Optional[int]]
    details: Mapped[Optional[str]]
    tries: Mapped[Optional[int]]
    flow: Mapped[Optional[str]]
    failure: Mapped[Optional[str]]
    visible: Mapped[bool] = mapped_column(insert_default=True)
    created: Mapped[str] = mapped_column(insert_default=joy.time.now)
    updated: Mapped[str] = mapped_column(insert_default=joy.time.now)


    @staticmethod
    def write(data):
        _data = data.copy()
        details = _data.get("details") or {}
        _data["details"] = json.dumps(details)
        flow = _data.get("flow") or []
        _data["flow"] = json.dumps(flow)
        return Task(**_data)

    def to_dict(self):
        data = {
            "id": self.id,
            "visible": self.visible,
            "created": self.created,
            "updated": self.updated
        }

        read_optional(self, data, optional)
        details = getattr(self, "details", "{}")
        data["details"] = json.loads(details)
        flow = getattr(self, "flow", "[]")
        data["flow"] = json.loads(flow)
        
        return data

    def update(self, data):
        self.visible = data["visible"]
        write_optional(self, data, optional)
        details = data.get("details") or {}
        self.details = json.dumps(details)
        flow = data.get("flow") or []
        self.flow = json.dumps(flow)
        self.updated = joy.time.now()