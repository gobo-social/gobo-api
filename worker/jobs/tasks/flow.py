import logging
import models
import joy
from tasks import Task
from . import helpers as h


# no-op to create stable start point for all flows.
# TODO: Maybe add some instrumentation here later.
def start_flow(task):
    pass


def flow_update_identity(task):
    identity = h.enforce("identity", task)
    platform = h.get_platform(identity)
    is_onboarding = task.details.get("is_onboarding", False)

    Task.send_flow(
        priority = task.priority,
        flow = [
            {
                "channel": platform, 
                "name": "get profile",
                "details": {
                    "identity": identity,
                    "is_shallow": is_onboarding
                }
            },
            {
                "channel": "default", 
                "name": "map profile",
            },
            {
                "channel": "default", 
                "name": "upsert profile"
            },
            {
                "channel": "default",
                "name": "filter publish only"  
            },
            {
                "channel": platform, 
                "name": "pull sources",
            },
            {
                "channel": "default", 
                "name": "map sources"
            },
            {
                "channel": "default", 
                "name": "upsert sources"
            },
            {
                "channel": "default", 
                "name": "reconcile sources",
            },
            {
                "channel": "default",
                "name": "flow - pull notifications"
            },
            {
                "channel": "default",
                "name": "flow - update identity feed"
            }
        ]
    )

def flow_update_identity_feed(task):
    identity = h.enforce("identity", task)
    platform = h.get_platform(identity)
    sources = h.enforce("sources", task)
    is_shallow = task.details.get("is_shallow", False)

    for source in sources:
        Task.send_flow(
            priority = task.priority,
            failure = "rollback cursor",
            flow = [
                {
                    "channel": "default",
                    "name": "check source lockout",
                    "details": {
                        "platform": platform,
                        "identity": identity,
                        "source": source
                    }
                },
                {
                    "channel": "default",
                    "name": "get source cursor"
                },
                {
                    "channel": platform, 
                    "name": "pull posts",
                    "details": {"is_shallow": is_shallow}
                },
                {
                    "channel": "default", 
                    "name": "map sources"
                },
                {
                    "channel": "default", 
                    "name": "upsert sources",
                },
                {
                    "channel": "default", 
                    "name": "map posts"
                },
                {
                    "channel": "default", 
                    "name": "upsert posts"
                },
            ]
        )


def flow_onboard_identity(task):
    identity = h.enforce("identity", task)

    Task.send(
        channel = "default",
        name = "flow - update identity",
        priority = task.priority,
        details = {
            "identity": identity,
            "is_onboarding": True
        }
    )



def flow_pull_sources(task):
    identity = h.enforce("identity", task)
    platform = h.get_platform(identity)

    Task.send_flow(
        priority = task.priority,
        flow = [
            {
                "channel": platform, 
                "name": "pull sources",
                "details": {
                    "identity": identity,
                }
            },
            {
                "channel": "default", 
                "name": "map sources"
            },
            {
                "channel": "default", 
                "name": "upsert sources"
            },
            {
                "channel": "default", 
                "name": "reconcile sources",
            }
        ]
    )



def flow_pull_posts(task):
    identity = h.enforce("identity", task)
    source = h.enforce("source", task)
    platform = h.get_platform(source)

    Task.send_flow(
        priority = task.priority,
        failure = "rollback cursor",
        flow = [
            {
                "channel": "default",
                "name": "check source lockout",
                "details": {
                    "identity": identity,
                    "source": source,
                }
            },
            {
                "channel": "default",
                "name": "get source cursor"
            },
            {
                "channel": platform, 
                "name": "pull posts",
            },
            {
                "channel": "default", 
                "name": "map sources"
            },
            {
                "channel": "default", 
                "name": "upsert sources",
            },
            {
                "channel": "default", 
                "name": "map posts"
            },
            {
                "channel": "default", 
                "name": "upsert posts"
            },
        ]
    )



def flow_pull_notifications(task):
    identity = h.enforce("identity", task)
    platform = h.get_platform(identity)

    Task.send_flow(
        priority = task.priority,
        failure = "rollback cursor",
        flow = [
            {
                "channel": "default",
                "name": "get notification cursor",
                "details": {
                  "identity": identity,
              }
            },
            {
                "channel": platform, 
                "name": "pull notifications"
            },
            {
                "channel": "default", 
                "name": "map sources"
            },
            {
                "channel": "default", 
                "name": "upsert sources"
            },
            {
                "channel": "default", 
                "name": "map posts"
            },
            {
                "channel": "default", 
                "name": "upsert posts"
            },
            {
                "channel": "default", 
                "name": "map notifications"
            },
            {
                "channel": "default", 
                "name": "upsert notifications"
            }
        ]
    )


def flow_dismiss_notification(task):
    identity = h.enforce("identity", task)
    platform = h.get_platform(identity)
    notification_id = h.enforce("notification_id", task)

    Task.send_flow(
        priority = task.priority,
        flow = [
            {
                "channel": platform, 
                "name": "dismiss notification",
                "details": {
                  "identity": identity,
                  "notification_id": notification_id
              }
            }
        ]
    )


# TODO: Does this belong in its own module category?
def filter_publish_only(task):
    identity = h.enforce("identity", task)
    
    excluded = ["linkedin"]
    if h.has_platform(excluded, identity):
        task.halt()
        return