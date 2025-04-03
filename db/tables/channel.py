import logging
import json
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
import joy
from ..base import Base
from .helpers import read_optional, write_optional

optional = [
    "name",
]

class Channel(Base):
    __tablename__ = "channel"

    id: Mapped[str] = mapped_column(String, primary_key=True, insert_default=joy.crypto.address)
    name: Mapped[Optional[str]]
    shards: Mapped[Optional[str]]
    paused: Mapped[bool] = mapped_column(insert_default=False)
    claimed: Mapped[bool] = mapped_column(insert_default=False)
    processing: Mapped[bool] = mapped_column(insert_default=False)
    sidecar: Mapped[Optional[str]]
    created: Mapped[str] = mapped_column(insert_default=joy.time.now)
    updated: Mapped[str] = mapped_column(insert_default=joy.time.now)


    @staticmethod
    def write(data):
        _data = data.copy()
        shards = _data.get("shards") or []
        _data["shards"] = json.dumps(shards)
        sidecar = _data.get("sidecar") or []
        _data["sidecar"] = json.dumps(sidecar)
        return Channel(**_data)

    def to_dict(self):
        data = {
            "id": self.id,
            "claimed": self.claimed,
            "paused": self.paused,
            "processing": self.processing,
            "created": self.created,
            "updated": self.updated
        }

        read_optional(self, data, optional)
        shards = getattr(self, "shards", "[]")
        data["shards"] = json.loads(shards)
        sidecar = getattr(self, "sidecar", "[]")
        data["sidecar"] = json.loads(sidecar)
        
        return data

    def update(self, data):
        self.paused = data["paused"]
        self.claimed = data["claimed"]
        self.processing = data["processing"]
        write_optional(self, data, optional)
        
        shards = data.get("shards") or []
        self.shards = json.dumps(shards)
        sidecar = data.get("sidecar") or []
        self.sidecar = json.dumps(sidecar)
        self.updated = joy.time.now()
