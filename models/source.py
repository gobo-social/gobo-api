import logging
import joy
from operator import itemgetter
from sqlalchemy import select
from db.base import Session
from db import tables
from .helpers import define_crud

Source = tables.Source
Link = tables.Link

add, get, update, remove, query, find, pluck, pull, scan = itemgetter(
    "add", "get", "update", "remove", "query", "find", "pluck", "pull", "scan"
)(define_crud(Source))


def upsert(data):
    with Session() as session:
        if data.get("base_url") is None or data.get("platform_id") is None:
            raise Exception("upsert requires source have base_url and platform_id")

        statement = select(Source) \
            .where(Source.base_url == data["base_url"]) \
            .where(Source.platform_id == data["platform_id"]) \
            .limit(1)

        row = session.scalars(statement).first()

        if row == None:
            row = Source.write(data)
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