import logging
import json
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
import joy
from ..base import Base
from .helpers import read_optional, write_optional

optional = []

class Delivery(Base):
    __tablename__ = "delivery"

    id:Mapped[str] = mapped_column(String, primary_key=True, insert_default=joy.crypto.address)
    person_id: Mapped[str]
    draft_id: Mapped[Optional[str]]
    proof_id: Mapped[Optional[str]]
    targets: Mapped[Optional[str]]
    created: Mapped[str] = mapped_column(insert_default=joy.time.now)
    updated: Mapped[str] = mapped_column(insert_default=joy.time.now)

    @staticmethod
    def write(data):
        _data = data.copy()

        targets = _data.get("targets", [])
        if targets is None:
            targets = []
        _data["targets"] = json.dumps(targets)      
        
        return Delivery(**_data)

    def to_dict(self):
        data = {
            "id": self.id,
            "person_id": self.person_id,
            "draft_id": self.draft_id,
            "proof_id": self.proof_id,
            "created": self.created,
            "updated": self.updated
        }

        targets = getattr(self, "targets", "[]")
        if targets is None:
            targets = "[]"
        data["targets"] = json.loads(targets)

        read_optional(self, data, optional)

        return data

    def update(self, data):
        self.person_id = data["person_id"]
        self.draft_id = data["draft_id"]
        self.proof_id = data["proof_id"]

        targets = data.get("targets", [])
        if targets is None:
            targets = []
        self.targets = json.dumps(targets)
        
        write_optional(self, data, optional)
        self.updated = joy.time.now()