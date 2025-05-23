import logging
import os
from os import environ
from datetime import timedelta
import models
import joy
from tasks import Task
from . import helpers as h

where = models.helpers.where
QueryIterator = models.helpers.QueryIterator


def prune_resources(task):
    Task.send("default", "prune draft files")
    Task.send("default", "prune drafts")
    Task.send("default", "prune posts")
    Task.send("default", "prune registrations")
    Task.send("default", "prune sources")
    Task.send("default", "prune notifications")
    Task.send("default", "prune proofs")
    Task.send("default", "prune delivery targets")
    Task.send("default", "prune deliveries")



def prune_draft_files(task):
    oldest_limit = joy.time.convert("date", "iso", 
        joy.time.nowdate() - timedelta(days=int(environ.get("MAXIMUM_RETENTION_DAYS")))
    )

    drafts = QueryIterator(
        model = models.draft_file,
        for_removal = True,
        wheres = [
            where("updated", oldest_limit , "lt")
        ]
    )

    for draft in drafts:
        filename = os.path.join(
            environ.get("UPLOAD_DIRECTORY"), 
            draft["id"]
        )
        
        if os.path.exists(filename):
            os.remove(filename)
        
        models.draft_file.remove(draft["id"])


def prune_drafts(task):
    oldest_limit = joy.time.convert("date", "iso", 
        joy.time.nowdate() - timedelta(days=int(environ.get("MAXIMUM_RETENTION_DAYS")))
    )

    drafts = QueryIterator(
        model = models.draft,
        for_removal = True,
        wheres = [
            where("updated", oldest_limit, "lt")
        ]
    )
    for draft in drafts:
        h.remove_draft(draft)


def prune_posts(task):
    oldest_limit = joy.time.convert("date", "iso", 
        joy.time.nowdate() - timedelta(days=int(environ.get("MAXIMUM_RETENTION_DAYS")))
    )

    posts = QueryIterator(
        model = models.post,
        for_removal = True,
        wheres = [
            where("updated", oldest_limit, "lt")
        ]
    )
    for post in posts:
        h.remove_post(post)



def prune_registrations(task):
    oldest_limit = joy.time.convert("date", "iso", 
        joy.time.nowdate() - timedelta(days=int(environ.get("MAXIMUM_RETENTION_DAYS")))
    )

    registrations = QueryIterator(
        model = models.registration,
        for_removal = True,
        wheres = [
            where("updated", oldest_limit, "lt")
        ]
    )
    for registration in registrations:
        models.registration.remove(registration["id"])



def prune_sources(task):
    oldest_limit = joy.time.convert("date", "iso", 
        joy.time.nowdate() - timedelta(days=int(environ.get("MAXIMUM_RETENTION_DAYS")))
    )

    # NOTE: This depends on the fact that we upsert sources opportunistically
    #       when they cross our path. So if updated is older than two weeks,
    #       no one is following it and there is no valid associated post.
    sources = QueryIterator(
        model = models.source,
        for_removal = True,
        wheres = [
            where("updated", oldest_limit, "lt")
        ]
    )

    for source in sources:
        h.remove_source(source)


def prune_notifications(task):
    oldest_limit = joy.time.convert("date", "iso", 
        joy.time.nowdate() - timedelta(days=int(environ.get("MAXIMUM_RETENTION_DAYS")))
    )

    notifications = QueryIterator(
        model = models.notification,
        for_removal = True,
        wheres = [
            where("created", oldest_limit, "lt")
        ]
    )

    for notification in notifications:
        h.remove_notification(notification)


def prune_proofs(task):
    oldest_limit = joy.time.convert("date", "iso", 
        joy.time.nowdate() - timedelta(days=int(environ.get("MAXIMUM_RETENTION_DAYS")))
    )

    proofs = QueryIterator(
        model = models.proof,
        for_removal = True,
        wheres = [
            where("updated", oldest_limit, "lt")
        ]
    )

    for proof in proofs:
        h.remove_proof(proof)

def prune_delivery_targets(task):
    oldest_limit = joy.time.convert("date", "iso", 
        joy.time.nowdate() - timedelta(days=int(environ.get("MAXIMUM_RETENTION_DAYS")))
    )

    targets = QueryIterator(
        model = models.delivery_target,
        for_removal = True,
        wheres = [
            where("updated", oldest_limit, "lt")
        ]
    )

    for target in targets:
        h.remove_delivery_target(target)

def prune_deliveries(task):
    oldest_limit = joy.time.convert("date", "iso", 
        joy.time.nowdate() - timedelta(days=int(environ.get("MAXIMUM_RETENTION_DAYS")))
    )

    deliveries = QueryIterator(
        model = models.delivery,
        for_removal = True,
        wheres = [
            where("updated", oldest_limit, "lt")
        ]
    )

    for delivery in deliveries:
        h.remove_delivery(delivery)