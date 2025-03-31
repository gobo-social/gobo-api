import logging
import models
import joy
from tasks import Task
from clients import Bluesky, Reddit
from . import helpers as h

where = models.helpers.where
QueryIterator = models.helpers.QueryIterator

def resolve_platform(url):
    if url == Bluesky.BASE_URL:
        return "bluesky"
    elif url == Reddit.BASE_URL:
        return "reddit"
    else:
        return "mastodon"
    
def label_identity_platform(task):
    identity = h.enforce("identity", task)
    if identity.get("platform", None) is None:
        identity["platform"] = resolve_platform(identity["base_url"])
        models.identity.update(identity["id"], identity)

def label_post_platform(task):
    post = h.enforce("post", task)
    if post.get("platform", None) is None:
        post["platform"] = resolve_platform(post["base_url"])
        models.post.update(post["id"], post)

def label_registration_platform(task):
    registration = h.enforce("registration", task)
    if registration.get("platform", None) is None:
        registration["platform"] = resolve_platform(registration["base_url"])
        models.registration.update(registration["id"], registration)

def label_source_platform(task):
    source = h.enforce("source", task)
    if source.get("platform", None) is None:
        source["platform"] = resolve_platform(source["base_url"])
        models.source.update(source["id"], source)


def boostrap_platform_labels(task):
    identities = QueryIterator(
        model = models.identity,
        per_page = 1
    )
    for identity in identities:
        Task.send(
            channel = "default",
            name = "label identity platform",
            details = {"identity": identity},
        )

    posts = QueryIterator(
        model = models.post,
    )
    for post in posts:
        Task.send(
            channel = "default",
            name = "label post platform",
            details = {"post": post},
        )

    registrations = QueryIterator(
        model = models.registration,
    )
    for registration in registrations:
        Task.send(
            channel = "default",
            name = "label registration platform",
            details = {"registration": registration},
        )

    sources = QueryIterator(
        model = models.source,
    )
    for source in sources:
        Task.send(
            channel = "default",
            name = "label source platform",
            details = {"source": source},
        )
