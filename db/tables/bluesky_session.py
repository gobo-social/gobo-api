from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
import joy
from ..base import Base
from .helpers import read_optional, write_optional

optional = [
    "identity_id",
    "base_url",
    "handle",
    "did",
    "access_token",
    "access_expires",
    "refresh_token",
    "refresh_expires"
]

class BlueskySession(Base):
    __tablename__ = "bluesky_session"

    id: Mapped[str] = mapped_column(String, primary_key=True, insert_default=joy.crypto.address)
    person_id: Mapped[str]
    identity_id: Mapped[Optional[str]]
    base_url: Mapped[Optional[str]]
    handle: Mapped[Optional[str]]
    did: Mapped[Optional[str]]
    access_token: Mapped[Optional[str]]
    access_expires: Mapped[Optional[str]]
    refresh_token: Mapped[Optional[str]]
    refresh_expires: Mapped[Optional[str]]
    created: Mapped[str] = mapped_column(insert_default=joy.time.now)
    updated: Mapped[str] = mapped_column(insert_default=joy.time.now)

    @staticmethod
    def write(data):
        return BlueskySession(**data)
    
    def to_dict(self):
        data = {
            "id": self.id,
            "person_id": self.person_id,
            "created": self.created,
            "updated": self.updated
        }

        read_optional(self, data, optional)

        return data

    def update(self, data):
        self.person_id = data["person_id"]
        self.identity_id = data["identity_id"]
        write_optional(self, data, optional)
        self.updated = joy.time.now()