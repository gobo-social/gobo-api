import logging
import models
import joy
from . import helpers as h
from .stale import handle_stale


def get_notification_cursor(task):
    identity = h.enforce("identity", task)    
    name = "read-cursor-notification"
    timeout = 0

    cursor = models.cursor.LoopCursor("identity", identity["id"], name)
    last_retrieved = cursor.stamp(timeout)

    # If this isn't a viable read, we need to bail.
    if last_retrieved == False:
        task.halt()
        return
    else:
      return {
        "cursor": cursor.to_json(),
        "last_retrieved": last_retrieved
      }

@handle_stale
def pull_notifications(task):
    client = h.get_client(task)
    cursor = h.get_cursor(task)
    last_retrieved = cursor.last_retrieved
    graph = client.list_notifications({"last_retrieved": last_retrieved})
    client.close()
    return {"graph": graph}

# No stale protection needed for unconnected client.
def map_notifications(task):
    client = h.get_unconnected_client(task)
    graph = h.enforce("graph", task)
    graph["sources"] = h.enforce("sources", task)
    graph["posts"] = h.enforce("posts", task)
    notifications = client.map_notifications(graph)
    return {"notifications": notifications}


def upsert_notifications(task):
    identity = h.enforce("identity", task)
    counter = models.counter.LoopCounter(
        "person",
        identity["person_id"], 
        "person-notification-count"
    )

    _notifications = h.enforce("notifications", task)
    notifications = []
    for item in _notifications:
        notification = models.notification.upsert(item)
        notifications.append(notification)
        
        if notification["active"] == True:
            counter.increment()

        models.link.upsert({
            "origin_type": "identity",
            "origin_id": identity["id"],
            "target_type": "notification",
            "target_id": notification["id"],
            "name": "notification-feed",
            "secondary": f"{notification['notified']}::{notification['id']}"
        })

        if notification["type"] == "mention":
            models.link.upsert({
                "origin_type": "identity",
                "origin_id": identity["id"],
                "target_type": "notification",
                "target_id": notification["id"],
                "name": "notification-mention-feed",
                "secondary": f"{notification['notified']}::{notification['id']}"
            })            

        if notification.get("post_id") is not None:
            models.link.upsert({
                "origin_type": "notification",
                "origin_id": notification["id"],
                "target_type": "post",
                "target_id": notification["post_id"],
                "name": "notifies",
                "secondary": f"{notification['notified']}::{notification['id']}"
            })

    # Store the updated unread notification count.
    counter.save()

    return {"notifications": notifications}

@handle_stale
def dismiss_notification(task):
    id = h.enforce("notification_id", task)
    client = h.get_client(task)
    
    notification = models.notification.get(id)
    if notification is None:
        logging.warn(f"cannot dismiss notification {id} because it was not found")
    
    client.dismiss_notification(notification)
    client.close()