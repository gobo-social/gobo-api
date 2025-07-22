import logging
from operator import itemgetter
from sqlalchemy import select
from db.base import Session
from db import tables
import joy
from .helpers import define_crud

Link = tables.Link

add, get, update, remove, query, find, pull, random = itemgetter(
    "add", "get", "update", "remove", "query", "find", "pull", "random"
)(define_crud(Link))


def upsert(data):
    with Session() as session:
        if data.get("origin_type") is None:
            raise Exception("upsert requires link have origin_type")
        if data.get("origin_id") is None:
            raise Exception("upsert requires link have origin_id")
        if data.get("target_type") is None:
            raise Exception("upsert requires link have target_type")
        if data.get("target_id") is None:
            raise Exception("upsert requires link have target_id")
        if data.get("name") is None:
            raise Exception("upsert requires link have name")


        statement = select(Link) \
            .where(Link.origin_type == data["origin_type"]) \
            .where(Link.origin_id == data["origin_id"]) \
            .where(Link.target_type == data["target_type"]) \
            .where(Link.target_id == data["target_id"]) \
            .where(Link.name == data["name"])

        # Secondary is not mandatory, but we need to avoid creating another
        # link if there is a match on this dimension.
        if data.get("secondary") is not None:
            statement = statement.where(Link.secondary == data["secondary"])
          
        statement = statement.limit(1)
       
        row = session.scalars(statement).first()

        if row == None:
            row = Link.write(data)
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
  

def find_and_remove(data):
    with Session() as session:
        statement = select(Link)
        for key, value in data.items():
            statement = statement.where(getattr(Link, key) == value)
        statement = statement.limit(1)

        row = session.scalars(statement).first()

        if row == None:
            return None
        else:
            out = row.to_dict()
            session.delete(row)
            session.commit()
            return out


class Lockout():
    def __init__(self, type, id, name):
        self.type = type
        self.id = id
        self.name = name
        self.link = None

    def body(self):
        return {
            "origin_type": self.type,
            "origin_id": self.id,
            "name": self.name,
            "target_type": self.type,
            "target_id": self.id          
        }
    
    def read(self):
        return find(self.body())

    def lock(self):
        return upsert(self.body())

    def unlock(self):
        return find_and_remove(self.body())