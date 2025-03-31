import logging
import joy
import models
from . import helpers as h


def remove_identity(task):
    identity = h.enforce("identity", task)
    h.remove_identity(identity)

def stale_identity(task):
    identity = h.enforce("identity", task)
    h.stale_identity(identity)