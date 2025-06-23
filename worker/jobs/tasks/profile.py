import logging
import models
from .stale import handle_stale
from . import helpers as h

@handle_stale
def get_profile(task):
    client = h.get_client(task)
    profile = client.get_profile_dict()
    client.close()
    return {"profile": profile}

# No stale protection needed for unconnected client.
def map_profile(task):
    client = h.get_unconnected_client(task)
    identity = h.enforce("identity", task)
    profile = h.enforce("profile", task)
    identity = client.map_profile({
        "profile": profile, 
        "identity": identity
    })
    return {"identity": identity}


def upsert_profile(task):
    identity = h.enforce("identity", task)
    models.identity.upsert(identity)