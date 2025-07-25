import logging
from operator import itemgetter
from sqlalchemy import select
from db import tables
from db.base import Session
from .helpers import define_crud

Identity = tables.Identity

add, get, update, remove, query, find, pull = itemgetter(
    "add", "get", "update", "remove", "query", "find", "pull"
)(define_crud(Identity))

def upsert(data):
    with Session() as session:
        if data.get("platform_id") is None:
            raise Exception("upsert requires identity have platform_id")
        if data.get("person_id") is None:
            raise Exception("upsert requires identity have person_id")

        statement = select(Identity) \
            .where(Identity.platform_id == data["platform_id"]) \
            .where(Identity.person_id == data["person_id"]) \
            .limit(1)

        row = session.scalars(statement).first()

        if row == None:
            row = Identity.write(data)
            session.add(row)
            session.flush()
            out = row.to_dict()
            session.commit()
            return out
        else:
            row.update(data)
            session.flush()
            out = row.to_dict()
            session.commit()
            return out