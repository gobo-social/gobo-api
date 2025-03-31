import logging
import joy
import models
from tasks import Task
from . import helpers as h
from . import notification as Notification

where = models.helpers.where
QueryIterator = models.helpers.QueryIterator


def test(task):
    logging.info(task.details)

def workbench(task):
    # identity = models.identity.get(501)
    identity = models.identity.get(454)
    Task.send(
        channel = "default",
        name = "flow - update identity",
        details = {
            "identity": identity
        },
    )
