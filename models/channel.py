import logging
from operator import itemgetter
from sqlalchemy import select
from db.base import Session
from db import tables
from .helpers import define_crud

Channel = tables.Channel

add, get, update, remove, query, find,  = itemgetter(
    "add", "get", "update", "remove", "query", "find"
)(define_crud(Channel))


def claim():
    with Session() as session:
        statement = select(Channel) \
            .where(Channel.claimed == False) \
            .limit(1) \
            .with_for_update(nowait = False)

        row = session.scalars(statement).first() 
        
        # If there are no unclaimed channels, we have to give up.
        if row is None:
            return None
        
        # But if we find one, we want to claim it during this transaction.
        data = row.to_dict()
        data["claimed"] = True
        row.update(data)
        session.commit()
        return row.to_dict()
