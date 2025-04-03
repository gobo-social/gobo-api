import json
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
import joy
from ..base import Base
from .helpers import read_optional, write_optional

optional = [
    "name"
]


class Store(Base):
    __tablename__ = "store"

    id: Mapped[str] = mapped_column(String, primary_key=True, insert_default=joy.crypto.address)
    person_id: Mapped[str]
    name: Mapped[Optional[str]]
    content: Mapped[Optional[str]]
    created: Mapped[str] = mapped_column(insert_default=joy.time.now)
    updated: Mapped[str] = mapped_column(insert_default=joy.time.now)

    @staticmethod
    def write(data):
        _data = data.copy()
        content = _data.get("content")
        if content is not None:
            _data["content"] = json.dumps(content)
        return Store(**_data)

    def to_dict(self):
        data = {
            "id": self.id,
            "person_id": self.person_id,
            "created": self.created,
            "updated": self.updated
        }

        read_optional(self, data, optional)
        
        content = getattr(self, "content", None)
        if content is not None:
            data["content"] = json.loads(content)
        
        return data

    def update(self, data):
        self.person_id = data["person_id"]
        write_optional(self, data, optional)

        content = data.get("content")
        if content != None:
            self.content = json.dumps(content)

        self.updated = joy.time.now()