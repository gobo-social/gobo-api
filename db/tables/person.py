import logging
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
import joy
from ..base import Base
from .helpers import read_optional, write_optional

optional = [
   "name"
]

class Person(Base):
    __tablename__ = "person"

    id: Mapped[str] = mapped_column(String, primary_key=True, insert_default=joy.crypto.address)
    authority_id: Mapped[Optional[str]]
    name: Mapped[Optional[str]]
    created: Mapped[str] = mapped_column(insert_default=joy.time.now)
    updated: Mapped[str] = mapped_column(insert_default=joy.time.now)

    @staticmethod
    def write(data):
        return Person(**data)

    def to_dict(self):
        data = {
            "id": self.id,
            "authority_id": self.authority_id,
            "created": self.created,
            "updated": self.updated
        }

        read_optional(self, data, optional)
        return data

    def update(self, data):
        self.authority_id = data["authority_id"]
        write_optional(self, data, optional)
        self.updated = joy.time.now()