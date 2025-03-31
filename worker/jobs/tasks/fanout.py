import logging
import models
import joy
from tasks import Task
from . import helpers as h

where = models.helpers.where
QueryIterator = models.helpers.QueryIterator

publish_only = [
    "linkedin"
]

# TODO: For identities from providers where we support publish-only behavior,
#   we don't want the fanout task to pick them up and run them through the
#   common read flows. Will this evolve over time?
def fanout_update_identity(task):
    platform = h.get_platform(task.details)

    wheres = [
        where("stale", False)
    ]
  
    if platform != "all":
        wheres.append(where("platform", platform))

    identities = QueryIterator(
        model = models.identity,
        wheres = wheres
    )
    for identity in identities:
        Task.send(
            channel = "default",
            name = "flow - update identity",
            priority = task.priority,
            details = {"identity": identity}
        )



def fanout_pull_notifications(task):
    platform = h.get_platform(task.details)
  
    wheres = [
        where("stale", False),
        where("platform", publish_only, "not in")
    ]
  
    if platform != "all":
        wheres.append(where("platform", platform))

    identities = QueryIterator(
        model = models.identity,
        wheres = wheres
    )
    for identity in identities:
        Task.send(
            channel = "default",
            name = "flow - pull notifications",
            priority = task.priority,
            details = {"identity": identity}
        )