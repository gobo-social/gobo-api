import logging
from operator import itemgetter
from sqlalchemy import select
from db.base import Session
from db import tables
from .helpers import define_crud

Task = tables.Task

add, get, update, remove, query, find,  = itemgetter(
    "add", "get", "update", "remove", "query", "find"
)(define_crud(Task))


def upsert(data):
    with Session() as session:
        if data.get("id") is None:
            raise Exception("upsert requires task have id")

        row = session.get(Task, data["id"])
        if row == None:
            row = Task.write(data)
            session.add(row)
            session.commit()
            return row.to_dict()
        else:
            row.update(data)
            session.commit()
            return row.to_dict()
        
def receive(channel, limit):
    with Session() as session:
        if channel is None:
            raise Exception("receiving tasks requires a channel definition")

        # We need to search for all visible tasks within this shard, sorted
        # by highest-priority, oldest-first. We use FOR UPDATE to lock
        # matching rows until we can update their visibility and complete
        # this transaction. 
        # 
        # SKIP LOCKED is useful for this channel access pattern, because we
        # can infer that locked rows are probably not what we're looking for
        # anyway, while staying eventually consistent.
        statement = select(Task) \
            .where(Task.channel == channel.name) \
            .where(Task.visible == True) \
            .where(Task.shard.in_(channel.shards)) \
            .order_by(Task.priority) \
            .order_by(Task.created) \
            .limit(limit) \
            .with_for_update(skip_locked = True, nowait = False)

        rows = session.scalars(statement).all()
        tasks = []
        for row in rows:
            data = row.to_dict()
            data["visible"] = False
            row.update(data)
            tasks.append(row.to_dict())
        
        # Commit releases the lock.
        session.commit()  
        return tasks
