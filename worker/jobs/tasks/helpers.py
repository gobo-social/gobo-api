import logging
import os
import models
import joy
from clients import Bluesky, Linkedin, Mastodon, Reddit, Smalltown
from tasks import Task

where = models.helpers.where
QueryIterator = models.helpers.QueryIterator
supported_platforms = [
  "all",
  "bluesky",
  "linkedin",
  "mastodon",
  "reddit",
  "smalltown"
]



def is_valid_platform(platform):
  return platform in supported_platforms

def generic_parameter(field, input):
    if isinstance(input, str):
        return input
    elif isinstance(input, dict):
        return input.get(field, None)
    else:
        return getattr(input, field, None)


def get_platform(input):
    platform = generic_parameter("platform", input)
    if not is_valid_platform(platform):
        raise Exception(f"{platform} is an invalid platform")
    return platform

def has_platform(list, input):
    platform = get_platform(input)
    return platform in list


def enforce(name, task):
    value = task.details.get(name, None)
    if value is None:
        raise Exception(f"task requires field {name} to be specified")
    return value


def _get_client(identity):
    platform = get_platform(identity)

    if platform == "bluesky":
        client = Bluesky(identity)
    elif platform == "linkedin":
        client = Linkedin(identity)
    elif platform == "mastodon":
        client = Mastodon(identity)
    elif platform == "reddit":
        client = Reddit(identity)
    elif platform == "smalltown":
        client = Smalltown(identity)
    else:
        raise Exception("unknown platform")
    
    return client

def get_client(task):
    identity = enforce("identity", task)
    client = _get_client(identity)
    client.login()
    return client

# This is for when we need access to an instance of the given platform's client
# class, but we don't need to login, and we don't need to full stale protections.
def get_unconnected_client(task):
    identity = enforce("identity", task)
    client = _get_client(identity)
    return client

def get_identity(id):
    return models.identity.get(id)

def get_cursor(task):
    string = enforce("cursor", task)
    return models.cursor.LoopCursor.from_json(string)

def read_draft_file(file):
    filename = os.path.join(os.environ.get("UPLOAD_DIRECTORY"), file["filename"])
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return f.read()
    else:
        logging.warning(f"Did not find file {filename}")


def reconcile_sources(task, identity, sources):
    desired_sources = set()
    for source in sources:
        desired_sources.add(source["id"])
    
    results = models.link.pull([
        where("origin_type", "identity"),
        where("origin_id", identity["id"]),
        where("target_type", "source"),
        where("name", "follows")
    ])
   
    current_sources = set()
    for result in results:
        current_sources.add(result["target_id"])

    difference = desired_sources - current_sources
    for source_id in difference:
        logging.info(f"For identity {identity['id']}, adding source {source_id}")
        Task.send(
            channel = "default",
            name = "follow",
            priority = task.priority,
            details = {
                "identity_id": identity["id"],
                "source_id": source_id
            }
        )

    difference = current_sources - desired_sources
    for source_id in difference:
        logging.info(f"For identity {identity['id']}, removing source {source_id}")
        Task.send(
            channel = "default",
            name = "unfollow",
            priority = task.priority,
            details = {
                "identity_id": identity["id"],
                "source_id": source_id
            }
        )


def attach_post(post):
    models.link.upsert({
        "origin_type": "source",
        "origin_id": post["source_id"],
        "target_type": "post",
        "target_id": post["id"],
        "name": "has-post",
        "secondary": f"{post['published']}::{post['id']}"
    })


def remove_draft(draft):
    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("origin_type", "draft"),
            where("origin_id", draft["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("target_type", "draft"),
            where("target_id", draft["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    models.draft.remove(draft["id"])


def remove_post(post):
    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("origin_type", "post"),
            where("origin_id", post["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("target_type", "post"),
            where("target_id", post["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    edges = QueryIterator(
        model = models.post_edge,
        for_removal = True,
        wheres = [
            where("post_id", post["id"])
        ]
    )
    for edge in edges:
        models.post_edge.remove(edge["id"])

    models.post.remove(post["id"])



def remove_source(source):
    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("origin_type", "source"),
            where("origin_id", source["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("target_type", "source"),
            where("target_id", source["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    models.source.remove(source["id"])


def remove_notification(notification):
    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("origin_type", "notification"),
            where("origin_id", notification["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("target_type", "notification"),
            where("target_id", notification["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    models.notification.remove(notification["id"])


def remove_identity(identity):
    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("origin_type", "identity"),
            where("origin_id", identity["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("target_type", "identity"),
            where("target_id", identity["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    bluesky = models.bluesky_session.find({
        "identity_id": identity["id"]
    })
    if bluesky is not None:
        models.bluesky_session.remove(bluesky["id"])

    linkedin = models.linkedin_session.find({
        "identity_id": identity["id"]
    })
    if linkedin is not None:
        models.linkedin_session.remove(linkedin["id"])

    models.identity.remove(identity["id"])



def remove_from_person(person_id, model):
    rows = QueryIterator(
        model = model,
        for_removal = True,
        wheres = [
            where("person_id", person_id),
        ]
    )
    for row in rows:
        model.remove(row["id"])


def remove_person(person_id):
    identities = QueryIterator(
        model = models.identity,
        for_removal = True,
        wheres = [
            where("person_id", person_id),
        ]
    )

    for identity in identities:
        remove_identity(identity)

    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("origin_type", "person"),
            where("origin_id", person_id)
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("target_type", "person"),
            where("target_id", person_id)
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    row = models.counter.find({
        "origin_type": "person",
        "origin_id": person_id,
    })
    if row is not None:
        models.counter.remove(row["id"])
    
    remove_from_person(person_id, models.delivery)
    remove_from_person(person_id, models.delivery_target)
    remove_from_person(person_id, models.draft)
    remove_from_person(person_id, models.draft_file)
    remove_from_person(person_id, models.filter)
    remove_from_person(person_id, models.gobo_key)
    remove_from_person(person_id, models.proof)
    remove_from_person(person_id, models.registration)
    remove_from_person(person_id, models.store)
    
    models.person.remove(person_id)
    

def stale_identity(identity):
    identity["stale"] = True
    models.identity.upsert(identity)

def remove_proof(proof):
    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("origin_type", "proof"),
            where("origin_id", proof["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("target_type", "proof"),
            where("target_id", proof["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    models.proof.remove(proof["id"])

def remove_delivery_target(target):
    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("origin_type", "delivery_target"),
            where("origin_id", target["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("target_type", "delivery_target"),
            where("target_id", target["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    models.delivery_target.remove(target["id"])

def remove_delivery(delivery):
    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("origin_type", "delivery"),
            where("origin_id", delivery["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    links = QueryIterator(
        model = models.link,
        for_removal = True,
        wheres = [
            where("target_type", "delivery"),
            where("target_id", delivery["id"])
        ]
    )
    for link in links:
        models.link.remove(link["id"])

    models.delivery.remove(delivery["id"])